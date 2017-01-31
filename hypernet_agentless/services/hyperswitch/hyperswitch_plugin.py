
from hypernet_agentless import hs_constants
from hypernet_agentless.db.hyperswitch import hyperswitch_db 
from hypernet_agentless.services.hyperswitch import config
from hypernet_agentless.services.hyperswitch import hyper_switch_api
from hypernet_agentless.extensions import hyperswitch
from hypernet_agentless.services.hyperswitch import providers

from neutron import manager
from neutron.db import common_db_mixin
from neutron.openstack.common import log as logging
from neutron.openstack.common import uuidutils

from sqlalchemy.orm import exc

LOG = logging.getLogger(__name__)


class HyperswitchPlugin(common_db_mixin.CommonDbMixin,
                        hyperswitch.HyperswitchPluginBase):

    supported_extension_aliases = [hs_constants.HYPERSWITCH]
    
    def __init__(self):
        if config.get_provider() in ['openstack', 'fs']:
            from providers import fs_impl
            self._provider_impl = fs_impl.FSProvider()
        elif config.get_provider() == 'aws':
            from providers import aws_impl
            self._provider_impl = aws_impl.AWSProvider()
        else:
            self._provider_impl = providers.null_impl.NULLProvider()
        self._hyper_switch_api = hyper_switch_api.HyperswitchAPI()
        self._vms_subnets = self._provider_impl.get_vms_subnet()
        self._hs_sg, self._vm_sg  = self._provider_impl.get_sgs()

    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

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
            'id': hs_db['id'],
            'tenant_id': hs_db['tenant_id'],
            'device_id': hs_db.get('device_id'),
            'flavor': hs_db.get('flavor'),
            'instance_id': hs_db.get('instance_id'),
            'instance_type': hs_db.get('instance_type'),
            'mgnt_ip': hs_db.get('mgnt_ip'),
            'data_ip': hs_db.get('data_ip'),
            'flavor': hs_db.get('flavor'),
            'vms_ips': vms_ip,
            'provider': hs_provider,
        }
        LOG.debug('_make_hyperswitch_dict result: %s' % res)
        return res

    def create_hyperswitch(self, context, hyperswitch):
        LOG.debug('hyper switch %s to create.' % hyperswitch)
        hs = hyperswitch[hs_constants.HYPERSWITCH]

        rabbit_hosts = None
        for rabbit_host in config.get_rabbit_hosts():
            if rabbit_hosts:
                rabbit_hosts = '%s, %s' % (rabbit_hosts, rabbit_host)
            else:
                rabbit_hosts = rabbit_host
        host = uuidutils.generate_uuid()

        user_data = {
            'rabbit_userid': config.get_rabbit_userid(),
            'rabbit_password': config.get_rabbit_password(),
            'rabbit_hosts': rabbit_hosts,
            'host': host,
            'network_mngt_interface': 'eth0',
        }

        net_list = [{
            'name': config.get_mgnt_network(),
            'security_group': [config.get_mgnt_security_group()]
        }]
        if config.get_data_network() != config.get_mgnt_network():
            net_list.append({
                'name': config.get_data_network(),
                'security_group': config.get_data_security_group()
            })
            user_data['network_data_interface'] = 'eth1'
        else:
            net_list[0]['security_group'].append(
                config.get_data_security_group())
            user_data['network_data_interface'] = 'eth0'

        for vm_subnet in self._vms_subnets:
            if vm_subnet != config.get_mgnt_network():
                user_data['network_vms_interface'] = 'eth2'
                net_list.append({
                    'name': vm_subnet,
                    'security_group': self._hs_sg
                })
            else:
                user_data['network_vms_interface'] = 'eth0'
                net_list[0]['security_group'].append(self._hs_sg)

        with context.session.begin(subtransactions=True):
            hs_provider = self._provider_impl.create_hyperswitch(
                user_data,
                hs.get('flavor'),
                net_list,
                host
            )
            vms_ips = []
            i_vms_ips = (hs_provider.get('vms_ips')
                        if hs_provider.get('vms_ips')
                        else hs.get('vms_ips'))
            for vms_ip in i_vms_ips:
                vms_ips.append(hyperswitch_db.HyperSwitchVmIp(
                    hyperswitch_id=host,
                    vms_ip=vms_ip['vms_ip'],
                    index=vms_ip['index']))
            hs_db = hyperswitch_db.HyperSwitch(
                id=host,
                tenant_id=hs.get('tenant_id'),
                device_id=hs.get('device_id'),
                flavor=(hs_provider.get('flavor')
                        if hs_provider.get('flavor')
                        else hs.get('flavor')),
                instance_id=(hs_provider.get('instance_id')
                             if hs_provider.get('instance_id')
                             else hs.get('instance_id')),
                instance_type=(hs_provider.get('instance_type')
                               if hs_provider.get('instance_type')
                               else hs.get('instance_type')),
                mgnt_ip=(hs_provider.get('mgnt_ip')
                         if hs_provider.get('mgnt_ip')
                         else hs.get('mgnt_ip')),
                data_ip=(hs_provider.get('data_ip')
                         if hs_provider.get('data_ip')
                         else hs.get('data_ip')),
                vms_ips=vms_ips
            )
            context.session.add(hs_db)
            hs =  self._make_hyperswitch_dict(hs_db, hs_provider)
            return hs

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
        if hs_db.get('host'):
            agents = self._core_plugin.get_agents(
                context,
                filters={'host': [hs_db.get('host')]})
            LOG.debug('agents to delete: %s' % agents)
            for agent in agents:
                self._core_plugin.delete_agent(context, agent.get('id'))

    def get_hyperswitchs(self, context, filters=None, fields=None,
                         sorts=None, limit=None, marker=None,
                         page_reverse=False):
        LOG.debug('get hyperswitch %s.' % filters)
        hyperswitchs_db = self._get_collection(
            context,
            hyperswitch_db.HyperSwitch,
            self._make_hyperswitch_dict,
            filters=filters, fields=fields,
            sorts=sorts,
            limit=limit,
            page_reverse=page_reverse)
        for hyperswitch_db in hyperswitchs_db:
            hyperswitch_db['provider'] = self._provider_impl.get_hyperswitch(
                hyperswitch_db['id'])
        return hyperswitchs_db

    def _make_agentlessport_dict(self,
                                 agentlessport_db,
                                 neutron_port=None,
                                 provider_net_int=None,
                                 hsservers=None):
        LOG.debug('_make_agentlessport_dict %s, %s, %s, %s' % (
            agentlessport_db, neutron_port, provider_net_int, hsservers))
        index = agentlessport_db['index']
        mac_address = None
        if neutron_port:
            mac_address = neutron_port['mac_address']
        hsservers_ip = None
        if hsservers:
            for hsserver in hsservers:
                if hsservers_ip:
                    hsservers_ip = '%s, %s' % (
                        hsservers_ip, hsserver['vms_ip_%d' % index])
                else:
                    hsservers_ip = '%s' % hsserver['vms_ip_%d' % index]
        res = {
            'id': agentlessport_db['id'],
            'tenant_id': agentlessport_db['tenant_id'],
            'device_id': agentlessport_db.get('device_id'),
            'port_id': agentlessport_db['id'],
            'name': agentlessport_db.get('name'),
            'index': index,
            'flavor': agentlessport_db.get('flavor'),
            'user_data': 'mac%d = %s\nhsservers%d = %s' % (
                index, mac_address, index, hsservers_ip),
            'provider': provider_net_int,
        }
        return res

    def create_agentlessport(self, context, agentlessport):
        al_port = agentlessport[hs_constants.AGENTLESSPORT]
        port_id = al_port.get('port_id')
        
        # Get the neutron port
        neutron_ports = self._core_plugin.get_ports(
            context,
            filters={'id': [port_id]})
        if not neutron_ports or len(neutron_ports) == 0:
            raise hyperswitch.AgentlessPortNeutronPortNotFound(
                agentlessport_id=port_id)

        if len(neutron_ports) != 1:
            raise hyperswitch.AgentlessPortNeutronPortMultipleFound(
                agentlessport_id=port_id)

        neutron_port = neutron_ports[0]

        index = al_port['index']

        device_id = neutron_port['device_id']
        tenant_id = neutron_port['tenant_id']
        flavor = al_port.get('flavor')
        if not flavor:
            flavor = config.get_hs_default_flavor()

        al_device_id = al_port.get('device_id')
        if al_device_id and al_device_id != device_id:
            raise hyperswitch.AgentlessPortBadDeviceId(
                neutron_device_id=device_id, device_id=al_device_id)

        with context.session.begin(subtransactions=True):
            # create in the provider
            net_int_provider = self._provider_impl.create_network_interface(
                port_id,
                self._vms_subnets[index],
                self._vm_sg)
            # create in DB
            agentlessport_db = hyperswitch_db.AgentlessPort(
                id=port_id,
                tenant_id=tenant_id,
                device_id=al_device_id,
                name=al_port.get('name'),
                provider_ip=net_int_provider['ip'],
                flavor=flavor,
                index=index)
            context.session.add(agentlessport_db)

        # retrieve the hyperswitchs to connect
        if config.get_level() == 'vm' or al_device_id:
            hsservers = self.get_hyperswitchs(
                context,
                filter={'device_id': [device_id]}
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
                filter={'tenant_id': [tenant_id]})
            if not hsservers or len(hsservers) == 0:
                hsservers = [self.create_hyperswitch(context, {
                    hs_constants.HYPERSWITCH: {
                        'tenant_id': tenant_id,
                        'flavor': flavor
                    }
                })]
        for hsserver in hsservers:
            self._provider_impl.start_hyperswitch(hsserver['id'])
        return self._make_agentlessport_dict(
            agentlessport_db, neutron_port, net_int_provider, hsservers)

    def _get_neutron_port(self, context, port_id):
        neutron_ports = self._core_plugin.get_ports(
            context,
            filters={'id': [port_id]})
        if not neutron_ports or len(neutron_ports) == 0:
            raise hyperswitch.AgentlessPortNotFound(
                agentlessport_id=port_id)
        if len(neutron_ports) > 1:
            raise hyperswitch.AgentlessPortNeutronPortMultipleFound(
                agentlessport_id=port_id)
        return neutron_ports[0]

    def _get_provider_net_int(self, context, port_id): 
        return self._provider_impl.get_network_interface(port_id)

    def _get_provider_hyperswitch_server(self, context, device_id, tenant_id):
        hsservers = self.get_hyperswitchs(
            context,
            filter={'device_id': [device_id]}
        )
        if not hsservers or len(hsservers) == 0:
            hsservers = self.get_hyperswitchs(
                context,
                filter={'tenant_id': [tenant_id]}
            )
        return hsservers

    def get_agentlessport(self, context, agentlessport_id, fields=None):
        LOG.debug('get agentless port %s.' % agentlessport_id)
        # hypernet agentless port
        try:
            agentlessport_db = self._get_by_id(
                context, hyperswitch_db.AgentlessPort, agentlessport_id)
        except exc.NoResultFound:
            raise hyperswitch.AgentlessPortNotFound(
                agentlessport_id=agentlessport_id)

        # neutron port
        neutron_port = self._get_neutron_port(context, agentlessport_id)

        # provider port
        provider_net_int = self._get_provider_net_int(
            context, agentlessport_id)

        # hyperswitch for this agent less port
        hsservers = self._get_provider_hyperswitch_server(
            neutron_port['device_id'], neutron_port['tenant_id']) 

        return self._make_agentlessport_dict(
            agentlessport_db, neutron_port, provider_net_int, hsservers)

    def delete_agentlessport(self, context, agentlessport_id):
        LOG.debug('removing agent less port %s.' % agentlessport_id)
        # remove from DB
        try:
            agentlessport_db = self._get_by_id(
                context, hyperswitch_db.AgentlessPort, agentlessport_id)
            with context.session.begin(subtransactions=True):
                context.session.delete(agentlessport_db)
        except exc.NoResultFound:
            pass

        # remove from provider
        self._provider_impl.delete_network_interface(agentlessport_id)

    def get_agentlessports(self, context, filters=None, fields=None,
                           sorts=None, limit=None, marker=None,
                           page_reverse=False):
        LOG.debug('get agent less ports %s.' % filters)
        # search id hypernet agent less port DB
        agentlessports_db = self._get_collection_query(
            context, hyperswitch_db.AgentlessPort,
            filters=filters, sorts=sorts, limit=limit)
        res = []
        # add neutron and provider info
        for agentlessport_db in agentlessports_db:
            port_id = agentlessport_db['id']
            neutron_port = self._get_neutron_port(context, port_id)
            provider_net_int = self._get_provider_net_int(
                context, port_id)
            hsservers = self._get_provider_hyperswitch_server(
                neutron_port['device_id'], neutron_port['tenant_id']) 
            res.append(self._make_agentlessport_dict(
                agentlessport_db, neutron_port, provider_net_int, hsservers))
        return res

