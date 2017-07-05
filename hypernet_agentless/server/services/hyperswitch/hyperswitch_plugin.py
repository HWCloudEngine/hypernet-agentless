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

from oslo_log import log as logging

from oslo_utils import uuidutils
from oslo_utils import importutils

from sqlalchemy.orm import exc
from hypernet_agentless.server.services import os_client


LOG = logging.getLogger(__name__)


class HyperswitchPlugin(common_db_mixin.CommonDbMixin,
                        hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = [hs_constants.HYPERSWITCH]

    def __init__(self):
        try:
            if config.provider() in ['openstack', 'fs']:
                clazz = (
                    'hypernet_agentless.server.services.'
                    'hyperswitch.providers.fs_impl.FSProvider'
                )
            elif config.provider() == 'aws':
                clazz = (
                    'hypernet_agentless.server.services.'
                    'hyperswitch.providers.aws_impl.AWSProvider'
                )
            else:
                clazz = (
                    'hypernet_agentless.server.services.'
                    'hyperswitch.providers.null_impl.NULLProvider'
                )
            self._provider_impl = importutils.import_object(clazz)
            self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
        except Exception as e:
            LOG.exception('execption = %s' % e)

    def _neutron_client(self, context):
        return os_client.get_neutron_client(context, admin=True)

    def _make_hyperswitch_dict(self,
                               hs_db,
                               hs_provider=None):
        LOG.debug('_make_hyperswitch_dict %s, %s' % (
            hs_db, hs_provider))
        vms_ips = []
        for vms_ip in hs_db.vms_ips:
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
                    break
            except:
                LOG.error('%s' % sys.exc_info()[0])
                time.sleep(5)
            finally:
                retry = retry + 1
                sock.close()

    def _get_net_list(self, context, tenant_id):
        net_list = [{
            'name': config.mgnt_network(),
            'security_group': [config.mgnt_security_group()]
        }]
        if config.data_network() == config.mgnt_network():
            net_list[0]['security_group'].append(
                config.data_security_group())
        else:
            net_list.append({
                'name': config.data_network(),
                'security_group': [config.data_security_group()]
            })
        hs_sg = self._get_hs_sg(tenant_id)
        subnet = self._get_tenant_subnet(context, tenant_id)
        net_list.append({
            'name': subnet,
            'security_group': [hs_sg]
        })
        return net_list

    def _get_userdata(self, hyperswitch_id):
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
                config.meta_metadata_proxy_shared_secret()),
            'pod_fip_address': config.pod_fip_address(),
            'isolate_relay_cidr': config.isolate_relay_cidr(),
            'first_openvpn_port': config.first_openvpn_port(),
            'max_win_nics': config.max_win_nics(),
        }

        if config.data_network() == config.mgnt_network():
            user_data['network_data_interface'] = 'eth0'
            user_data['network_vms_interface'] = 'eth1'
        else:
            user_data['network_data_interface'] = 'eth1'
            user_data['network_vms_interface'] = 'eth2'
        return user_data

    def _get_hs_sg(self, tenant_id):
        self._provider_impl.get_sgs(tenant_id)[0]

    def _get_vm_sg(self, tenant_id):
        self._provider_impl.get_sgs(tenant_id)[1]

    def _get_tenant_subnet(self, context, tenant_id):
        providersubnetpools = self.get_providersubnetpools(
            context, filters={'used_by': [tenant_id]})['providersubnetpools']
        if len(providersubnetpools) == 0:
            with context.session.begin(subtransactions=True):
                #TODO: add a try/except to prevent
                # take a random cidr 
                query = context.session.query(
                    hyperswitch_db.ProviderSubnetPool.id)
                query = query.filter(
                        hyperswitch_db.ProviderSubnetPool.used_by is None
                    )
                query = query.limit(1).with_for_update()
                context.session.update(
                    hyperswitch_db.ProviderSubnetPool).values(
                        {
                            'used_by': tenant_id
                        }).where(
                            (hyperswitch_db.ProviderSubnetPool.id == 
                                query.as_scalar()))
            providersubnetpools = self.get_providersubnetpools(
                context, filters={
                    'used_by': [tenant_id]})['providersubnetpools']
        if len(providersubnetpools) == 0:
            raise hyperswitch.ProviderSubnetPoolUseFailed(
                tenant_id=tenant_id)
        else:
            providersubnetpool = providersubnetpools[0]
        return providersubnetpool['provider_subnet']['id']


    def create_hyperswitch(self, context, hyperswitch):
        LOG.debug('hyper switch %s to create.' % hyperswitch)
        hs = hyperswitch[hs_constants.HYPERSWITCH]

        hyperswitch_id = uuidutils.generate_uuid()

        user_data = self._get_userdata(hyperswitch_id)
        net_list = self._get_net_list(context, hs.get('tenant_id'))

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
            user_data = self._get_userdata(hyperswitch_id)
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
        agents = self._neutron_client(context).list_agents(
            host=[hs_db.id])['agents']
        LOG.debug('agents to delete: %s' % agents)
        for agent in agents:
            self._neutron_client(context).delete_agent(agent.get('id'))

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
            'user_data': 'mac%d = %s\nhsservers%d = %s\nport%d = %s' % (
                index, mac_address,
                index, hsservers_ip,
                index, config.first_openvpn_port() + index,
            ),
            'provider': provider_net_int,
        }
        return res

    def create_providerport(self, context, providerport):
        p_port = providerport[hs_constants.PROVIDERPORT]
        port_id = p_port.get('port_id')

        # Get the neutron port
        search_opts = {'id': port_id}
        neutron_ports = self._neutron_client(context).list_ports(
            **search_opts)['ports']
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
            vm_sg = self._get_vm_sg(tenant_id)
            subnet = self._get_tenant_subnet(context, tenant_id)
            # create in the provider
            net_int_provider = self._provider_impl.create_network_interface(
                port_id,
                subnet,
                vm_sg)
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
        neutron_ports = self._neutron_client(context).list_ports(
            id=[port_id])['ports']
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
            self._hyper_switch_api.unplug_vif(
                context, providerport_id, providerport_db.index)
        except exc.NoResultFound:
            pass
        finally:
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

    def _make_providersubnetpool_dict(self, providersubnetpool_db):
        LOG.debug('_make_providersubnetpool_dict %s' % (
            providersubnetpool_db))
        provider_subnet = None
        if providersubnetpool_db.used_by:
            name = 'subnet_%s' % providersubnetpool_db.used_by

            provider_subnet = {
                'name': name,
                'id': self._provider_impl.get_subnet(
                    name,
                    providersubnetpool_db.cidr)
            }
        return {
            'id': providersubnetpool_db.id,
            'cidr': providersubnetpool_db.cidr,
            'used_by': providersubnetpool_db.used_by,
            'provider_subnet': provider_subnet
        }

    def create_providersubnetpool(self, context, providersubnetpool):
        LOG.debug('create_providersubnetpool %s.' % providersubnetpool)
        providersubnetpool = providersubnetpool['providersubnetpool']
        with context.session.begin(subtransactions=True):
            # create in DB
            providersubnetpool_db = hyperswitch_db.ProviderSubnetPool(
                id=uuidutils.generate_uuid(),
                tenant_id=providersubnetpool['tenant_id'],
                cidr=providersubnetpool['cidr'],
                used_by=providersubnetpool['used_by'],
            )
            context.session.add(providersubnetpool_db)
        return self._make_providersubnetpool_dict(
            providersubnetpool_db)

    def get_providersubnetpool(self,
                               context,
                               providersubnetpool_id,
                               fields=None):
        LOG.debug('get_providersubnetpool %s.' % providersubnetpool_id)
        try:
            providersubnetpool_db = self._get_by_id(
                context,
                hyperswitch_db.ProviderSubnetPool,
                providersubnetpool_id)
        except exc.NoResultFound:
            raise hyperswitch.ProviderSubnetPoolNotFound(
                providersubnetpool_id=providersubnetpool_id)

        return self._make_providersubnetpool_dict(
            providersubnetpool_db)

    def update_providersubnetpool(self,
                                  context,
                                  providersubnetpool_id,
                                  providersubnetpool):
        LOG.debug('update_providersubnetpool %s (%s) to update.' % (
            providersubnetpool_id, providersubnetpool))
        providersubnetpool_db = self._get_by_id(
            context, hyperswitch_db.ProviderSubnetPool, providersubnetpool_id)

        psubnetpool = providersubnetpool['providersubnetpool']
        with context.session.begin(subtransactions=True):
            providersubnetpool_db.update(psubnetpool)

        return self._make_providersubnetpool_dict(
            providersubnetpool_db)

    def delete_providersubnetpool(self, context, providersubnetpool_id):
        LOG.debug('delete_providersubnetpool %s.' % providersubnetpool_id)
        # remove from DB
        try:
            providersubnetpool_db = self._get_by_id(
                context,
                hyperswitch_db.ProviderSubnetPool,
                providersubnetpool_id)
            with context.session.begin(subtransactions=True):
                context.session.delete(providersubnetpool_db)
        except exc.NoResultFound:
            pass
        finally:
            # TODO: maybe remove from provider
            pass

    def get_providersubnetpools(self, context, filters=None, fields=None,
                                sorts=None, limit=None, marker=None,
                                page_reverse=False):
        LOG.debug('get_providersubnetpools %s.' % filters)
        providersubnetpools_db = self._get_collection_query(
            context, hyperswitch_db.ProviderSubnetPool,
            filters=filters, sorts=sorts, limit=limit)
        res = []
        for providersubnetpool_db in providersubnetpools_db:
            res.append(self._make_providersubnetpool_dict(
                providersubnetpool_db))
        return res
