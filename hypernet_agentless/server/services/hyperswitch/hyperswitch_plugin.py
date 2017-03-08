import json
import socket
import sys
import time

from hypernet_agentless.common import hs_constants
from hypernet_agentless.server.db import common_db_mixin
from hypernet_agentless.server.db.hyperswitch import hyperswitch_db 
from hypernet_agentless.server import config
from hypernet_agentless.server.services.hyperswitch import hyper_switch_api
from hypernet_agentless.server.extensions import hyperswitch
from hypernet_agentless.server.services.hyperswitch import providers

from oslo_log import log as logging

from oslo_utils import uuidutils

from sqlalchemy.orm import exc
from hypernet_agentless.server.services import os_client


LOG = logging.getLogger(__name__)


class HyperswitchPlugin(common_db_mixin.CommonDbMixin,
                        hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = [hs_constants.HYPERSWITCH]
    
    def __init__(self):
        try:
            if config.provider() in ['openstack', 'fs']:
                from providers import fs_impl
                self._provider_impl = fs_impl.FSProvider()
            elif config.provider() == 'aws':
                from providers import aws_impl
                self._provider_impl = aws_impl.AWSProvider()
            else:
                from providers import null_impl
                self._provider_impl = null_impl.NULLProvider()
            self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
            self._vms_subnets = self._provider_impl.get_vms_subnet()
            self._hs_sg, self._vm_sg  = self._provider_impl.get_sgs()
        except:
            LOG.exception('rrr')

    @property
    def _neutron_client(self):
        return os_client.get_neutron_client('neutron')

    def _make_hyperswitch_dict(self,
                               hs_db,
                               hs_provider=None):
        LOG.debug('_make_hyperswitch_dict %s, %s' % (
            hs_db, hs_provider))
        vms_ips = []
        for vms_ip in  hs_db.vms_ips:
            vms_ips.append({
                'vms_ip': vms_ip.vms_ip,
                'index': vms_ip.index
            })
        res = {
            'id': hs_db.id,
            'name': hs_db.name,
            'tenant_id': hs_db.tenant_id,
            'device_id': hs_db.device_id,
            'flavor': hs_db.flavor,
            'instance_id': hs_db.instance_id,
            'instance_type': hs_db.instance_type,
            'mgnt_ip': hs_db.mgnt_ip,
            'data_ip': hs_db.data_ip,
            'vms_ips': vms_ips,
            'provider': hs_provider,
        }
        LOG.debug('_make_hyperswitch_dict result: %s' % res)
        return res

    def _get_attr(self, provider_obj, param_obj, attr):
        if provider_obj and attr in provider_obj:
            return provider_obj[attr]
        return param_obj.get(attr)

    def _send(self, host, port, data):
        retry = 0
        data = json.encoder.JSONEncoder().encode((data))
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                LOG.debug('%d: try to send to %s:%s (%s)' % (
                    retry, host, port, data))
                sock.connect((host, port))
                sock.sendall(data + "\n.\n")
                received = sock.recv(1024)
                if received == 'OK' or retry == 20:
                    break;
            except:
                LOG.error('%s' % sys.exc_info()[0])
                time.sleep(5)
            finally:
                retry = retry + 1
                sock.close()

    def _get_userdata_net_list(self, hyperswitch_id):
        user_data = {
            'rabbit_userid': config.rabbit_userid(),
            'rabbit_password': config.rabbit_password(),
            'rabbit_hosts': config.rabbit_hosts(),
            'host': hyperswitch_id,
            'network_mngt_interface': 'eth0',
            'auth_uri': config.meta_auth_uri(),
            'auth_url': config.meta_auth_uri(),
            'auth_region': config.meta_auth_region(),
            'admin_tenant_name': config.meta_admin_tenant_name(),
            'admin_user': config.meta_admin_user(),
            'admin_password': config.meta_admin_password(),
            'nova_metadata_ip': config.controller_name(),
            'controller_ip': config.controller_ip(),
            'controller_name': config.controller_name(),
            'controller_host': config.controller_host(),
            'metadata_proxy_shared_secret': (
                config.meta_metadata_proxy_shared_secret())
        }

        net_list = [{
            'name': config.mgnt_network(),
            'security_group': [config.mgnt_security_group()]
        }]
        i = 0
        if config.data_network() == config.mgnt_network():
            net_list[0]['security_group'].append(
                config.data_security_group())
        else:
            i = i + 1
            net_list.append({
                'name': config.data_network(),
                'security_group': [config.data_security_group()]
            })
        user_data['network_data_interface'] = 'eth%d' % i

        for vm_subnet in self._vms_subnets:
            if vm_subnet == config.mgnt_network():
                if 'network_vms_interface' in user_data:
                    user_data['network_vms_interface'] = '%s, eth0' % (
                        user_data['network_vms_interface'])
                else:
                    user_data['network_vms_interface'] = 'eth0'
                net_list[0]['security_group'].append(self._hs_sg)
            elif vm_subnet == config.data_network():
                if 'network_vms_interface' in user_data:
                    user_data['network_vms_interface'] = '%s, eth1' % (
                        user_data['network_vms_interface'])
                else:
                    user_data['network_vms_interface'] = 'eth1'
                net_list[1]['security_group'].append(self._hs_sg)
            else:
                i = i + 1
                if 'network_vms_interface' in user_data:
                    user_data['network_vms_interface'] = '%s, eth%d' % (
                        user_data['network_vms_interface'], i)
                else:
                    user_data['network_vms_interface'] = 'eth%d' % i
                net_list.append({
                    'name': vm_subnet,
                    'security_group': [self._hs_sg]
                })
        return user_data, net_list

    def create_hyperswitch(self, context, hyperswitch):
        LOG.debug('hyper switch %s to create.' % hyperswitch)
        hs = hyperswitch[hs_constants.HYPERSWITCH]

        hyperswitch_id = uuidutils.generate_uuid()

        user_data, net_list = self._get_userdata_net_list(hyperswitch_id)

        with context.session.begin(subtransactions=True):
            hs_provider = self._provider_impl.create_hyperswitch(
                user_data,
                hs.get('flavor'),
                net_list,
                hyperswitch_id
            )
            try:
                vms_ips = []
                i_vms_ips = self._get_attr(hs_provider, hs, 'vms_ips')
                if i_vms_ips:
                    for vms_ip in i_vms_ips:
                        vms_ips.append(hyperswitch_db.HyperSwitchVmsIp(
                            hyperswitch_id=hyperswitch_id,
                            vms_ip=vms_ip['vms_ip'],
                            index=vms_ip['index']))
                hs_db = hyperswitch_db.HyperSwitch(
                    id=hyperswitch_id,
                    tenant_id=hs.get('tenant_id'),
                    name=hs.get('name'),
                    device_id=hs.get('device_id'),
                    flavor=self._get_attr(hs_provider, hs, 'flavor'),
                    instance_id=self._get_attr(hs_provider,
                                               hs,
                                               'instance_id'),
                    instance_type=self._get_attr(hs_provider,
                                                 hs,
                                                 'instance_type'),
                    mgnt_ip=self._get_attr(hs_provider, hs, 'mgnt_ip'),
                    data_ip=self._get_attr(hs_provider, hs, 'data_ip'),
                    vms_ips=vms_ips
                )
                context.session.add(hs_db)
                if 'mgnt_ip' in hs_provider:
                    user_data['mgnt_ip'] = hs_provider['mgnt_ip']
                    user_data['data_ip'] = hs_provider['data_ip']
                    self._send(
                        hs_provider['mgnt_ip'], 8080, user_data)
                return self._make_hyperswitch_dict(hs_db, hs_provider)
            except:
                self._provider_impl.delete_hyperswitch(hyperswitch_id)
                raise

    def get_hyperswitch(self, context, hyperswitch_id, fields=None):
        LOG.debug('hyperswitch %s to show.' % hyperswitch_id)

        # hyperswitch db
        try:
            hs_db = self._get_by_id(
                context, hyperswitch_db.HyperSwitch, hyperswitch_id)
        except exc.NoResultFound:
            raise hyperswitch.HyperswitchNotFound(
                hyperswitch_id=hyperswitch_id)

        # hyperswitch provider
        hs_provider = self._provider_impl.get_hyperswitch(hyperswitch_id)

        return self._make_hyperswitch_dict(hs_db, hs_provider)

    def update_hyperswitch(self,
                           context,
                           hyperswitch_id,
                           hyperswitch):
        LOG.debug('hyperswitch %s (%s) to update.' % (
            hyperswitch_id, hyperswitch))
        hs_db = self._get_by_id(
            context, hyperswitch_db.HyperSwitch, hyperswitch_id)

        hs = hyperswitch[hs_constants.HYPERSWITCH]
        with context.session.begin(subtransactions=True):
            hs_db.update(hs)
            
        # hyperswitch provider
        hs_provider = self._provider_impl.get_hyperswitch(hyperswitch_id)
        if hs_provider:
            user_data, _ = self._get_userdata_net_list(hyperswitch_id)
            user_data['mgnt_ip'] = hs_provider['mgnt_ip']
            user_data['data_ip'] = hs_provider['data_ip']
            self._send(hs_db.mgnt_ip, 8080, user_data)
        return self._make_hyperswitch_dict(hs_db, hs_provider)

    def delete_hyperswitch(self, context, hyperswitch_id):
        LOG.debug('hyperswitch %s to delete.' % hyperswitch_id)
        # remove from DB
        try:
            hs_db = self._get_by_id(
                context, hyperswitch_db.HyperSwitch, hyperswitch_id)
            with context.session.begin(subtransactions=True):
                context.session.delete(hs_db)
        except exc.NoResultFound:
            pass

        # remove from provider
        self._provider_impl.delete_hyperswitch(hyperswitch_id)

        # remove agents
        agents = self._neutron_client.list_agents(
            host=[hs_db.id])
        LOG.debug('agents to delete: %s' % agents)
        for agent in agents:
            self._neutron_client.delete_agent(agent.get('id'))

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug('get hyperswitch %s.' % filters)
        hss_db = self._get_collection(
            context,
            hyperswitch_db.HyperSwitch,
            self._make_hyperswitch_dict,
            filters=filters, fields=fields,
            sorts=sorts,
            limit=limit,
            page_reverse=page_reverse)
        for hs_db in hss_db:
            hs_db['provider'] = self._provider_impl.get_hyperswitch(
                hs_db['id'])
        return hss_db

    def _make_providerport_dict(self,
                                providerport_db,
                                neutron_port=None,
                                provider_net_int=None,
                                hsservers=None):
        LOG.debug('_make_providerport_dict %s, %s, %s, %s' % (
            providerport_db, neutron_port, provider_net_int, hsservers))
        index = providerport_db.index
        mac_address = None
        if neutron_port:
            mac_address = neutron_port['mac_address']
        hsservers_ip = None
        if hsservers:
            for hsserver in hsservers:
                vms_ips = hsserver.get('vms_ips')
                if vms_ips:
                    for vms_ip in vms_ips:
                        if vms_ip['index'] == index: 
                            if hsservers_ip:
                                hsservers_ip = '%s, %s' % (
                                    hsservers_ip, vms_ip['vms_ip'])
                            else:
                                hsservers_ip = '%s' % vms_ip['vms_ip']
        res = {
            'id': providerport_db.id,
            'tenant_id': providerport_db.tenant_id,
            'device_id': providerport_db.device_id,
            'port_id': providerport_db.id,
            'name': providerport_db.name,
            'type': providerport_db.type,
            'index': index,
            'flavor': providerport_db.flavor,
            'user_data': 'mac%d = %s\nhsservers%d = %s' % (
                index, mac_address, index, hsservers_ip),
            'provider': provider_net_int,
        }
        return res

    def create_providerport(self, context, providerport):
        p_port = providerport[hs_constants.PROVIDERPORT]
        port_id = p_port.get('port_id')
        
        # Get the neutron port
        neutron_ports = self._neutron_client.list_ports(
            id=[port_id])
        if not neutron_ports or len(neutron_ports) == 0:
            raise hyperswitch.ProviderPortNeutronPortNotFound(
                providerport_id=port_id)

        if len(neutron_ports) != 1:
            raise hyperswitch.ProviderPortNeutronPortMultipleFound(
                providerport_id=port_id)

        neutron_port = neutron_ports[0]

        index = p_port['index']

        device_id = neutron_port['device_id']
        tenant_id = neutron_port['tenant_id']
        flavor = p_port.get('flavor')
        if not flavor:
            flavor = config.hs_default_flavor()

        al_device_id = p_port.get('device_id')
        if al_device_id and al_device_id != device_id:
            raise hyperswitch.ProviderPortBadDeviceId(
                neutron_device_id=device_id, device_id=al_device_id)

        # retrieve the hyperswitchs to connect
        if config.level() == 'vm' or al_device_id:
            hsservers = self.get_hyperswitchs(
                context,
                filters={'device_id': [device_id]}
            )
            if not hsservers or len(hsservers) == 0:
                hsservers = [self.create_hyperswitch(context, {
                    hs_constants.HYPERSWITCH: {
                        'device_id': device_id,
                        'flavor': flavor
                    }
                })]
        else:
            hsservers = self.get_hyperswitchs(
                context,
                filters={'tenant_id': [tenant_id]})
            if not hsservers or len(hsservers) == 0:
                hsservers = [self.create_hyperswitch(context, {
                    hs_constants.HYPERSWITCH: {
                        'tenant_id': tenant_id,
                        'flavor': flavor
                    }
                })]

        with context.session.begin(subtransactions=True):
            # create in the provider
            net_int_provider = self._provider_impl.create_network_interface(
                port_id,
                self._vms_subnets[index],
                self._vm_sg)
            try:
                # create in DB
                providerport_db = hyperswitch_db.ProviderPort(
                    id=port_id,
                    tenant_id=tenant_id,
                    device_id=al_device_id,
                    name=p_port.get('name'),
                    type=p_port.get('type'),
                    provider_ip=self._get_attr(
                        net_int_provider, p_port, 'provider_ip'),
                    flavor=flavor,
                    index=index)
                context.session.add(providerport_db)
            except:
                self._provider_impl.delete_network_interface(port_id)
                raise

        for hsserver in hsservers:
            self._provider_impl.start_hyperswitch(hsserver['id'])
        return self._make_providerport_dict(
            providerport_db, neutron_port, net_int_provider, hsservers)

    def _get_neutron_port(self, context, port_id):
        neutron_ports = self._neutron_client.list_ports(
            id=[port_id])
        if not neutron_ports or len(neutron_ports) == 0:
            raise hyperswitch.ProviderPortNotFound(
                providerport_id=port_id)
        if len(neutron_ports) > 1:
            raise hyperswitch.ProviderPortNeutronPortMultipleFound(
                providerport_id=port_id)
        return neutron_ports[0]

    def _get_provider_net_int(self, context, port_id): 
        return self._provider_impl.get_network_interface(port_id)

    def _get_provider_hyperswitch_server(self, context, device_id, tenant_id):
        hsservers = self.get_hyperswitchs(
            context,
            filters={'device_id': [device_id]}
        )
        if not hsservers or len(hsservers) == 0:
            hsservers = self.get_hyperswitchs(
                context,
                filters={'tenant_id': [tenant_id]}
            )
        return hsservers

    def get_providerport(self, context, providerport_id, fields=None):
        LOG.debug('get provider port %s.' % providerport_id)
        # hypernet provider port
        try:
            providerport_db = self._get_by_id(
                context, hyperswitch_db.ProviderPort, providerport_id)
        except exc.NoResultFound:
            raise hyperswitch.ProviderPortNotFound(
                providerport_id=providerport_id)

        # neutron port
        neutron_port = self._get_neutron_port(context, providerport_id)

        # provider port
        provider_net_int = self._get_provider_net_int(
            context, providerport_id)

        # hyperswitch for this agent less port
        hsservers = self._get_provider_hyperswitch_server(
            context, neutron_port['device_id'], neutron_port['tenant_id']) 

        return self._make_providerport_dict(
            providerport_db, neutron_port, provider_net_int, hsservers)

    def delete_providerport(self, context, providerport_id):
        LOG.debug('removing agent less port %s.' % providerport_id)
        # remove from DB
        try:
            providerport_db = self._get_by_id(
                context, hyperswitch_db.ProviderPort, providerport_id)
            with context.session.begin(subtransactions=True):
                context.session.delete(providerport_db)
        except exc.NoResultFound:
            pass

        # remove from provider
        self._provider_impl.delete_network_interface(providerport_id)

    def get_providerports(self, context, filters=None, fields=None,
                           sorts=None, limit=None, marker=None,
                           page_reverse=False):
        LOG.debug('get agent less ports %s.' % filters)
        # search id hypernet agent less port DB
        providerports_db = self._get_collection_query(
            context, hyperswitch_db.ProviderPort,
            filters=filters, sorts=sorts, limit=limit)
        res = []
        # add neutron and provider info
        for providerport_db in providerports_db:
            port_id = providerport_db['id']
            neutron_port = self._get_neutron_port(context, port_id)
            provider_net_int = self._get_provider_net_int(
                context, port_id)
            hsservers = self._get_provider_hyperswitch_server(
                context, neutron_port['device_id'], neutron_port['tenant_id']) 
            res.append(self._make_providerport_dict(
                providerport_db, neutron_port, provider_net_int, hsservers))
        return res