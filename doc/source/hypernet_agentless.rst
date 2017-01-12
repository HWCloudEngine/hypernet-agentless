==================
HyperNet Agentless
==================

Hyper Network Background
========================

In the current hybrid cloud solution, a cloud provider is managed by an openstack instance (called jacket, Embedded Openstack or Cascaded) that translates the openstack APIs and entities to the provider APIs and entities.

The Hyper Network, Hyper Port, Hyper Security Group are cascaded neutron entities.

The provider Virtual Machines, Provider Networks and Provider Security groups are provided by the cloud provider (AWS or openstack)

The requirements for an agent less solution is to connect a Provider Virtual Machine with small and standard changes in this virtual machine to the hyper network implementing the cascaded neutron functionalities (L2: Hyper IP and Network, L3: Hyper Subnet, Hyper SG etc...)

The challenge is that the cloud provider does not provide the whole neutron functionality and should be implemented by agents or extra provider virtual machine.

Solution:
=========

The presented solution for the data path is based on a standard VPN client installed in the Provider VM. This VPN connects to a VPN server installed on an extra Provider Virtual Machine. This Provider Virtual Machine is called 'hyperswith' (the entry point of the Hyper Network) and implement all the Neutron functionalities. The VPN client receives the Hyper IP with DHCP protocol on the VPN termination and replace the network routes the the hyper network one.

Data Path Diagram::

  +------------------------+                     +------------------------+
  + VM with OpenVPN client +       ....          + VM with OpenVPN client +
  +----------+-------------+                     +------------+-----------+
             |                                                |
             +----+        OpenVPN connectivity      +--------+
                  |                                  +
           +------+------+                    +------+------+
           + Hyperswitch +        ....        + Hyperswitch +
           +------+------+                    +------+------+
                  |   VxLan/GRE/Geneve tunneling     |
                  +----------------+-----------------+
                                   |
                               +---+----+
                               | Jacket |
                               +--------+

The implementation is based on a Neutron extension and plugin in the jacket and an agent installed in the extra hyperswitch VM. The hypernet agent less Neutron plugin implements: 
   - hyperswitch APIs to manage the extra provider virtual machine (hyperswitches)
   - agentlessport APIs to define a hyper port as an agent less port
   - Messaging supplementary API for the hyperswitch agent control communication.

Control Path Diagram::

  +------------------------+                     +------------------------+
  + VM with OpenVPN client +       ....          + VM with OpenVPN client +
  +----------+-------------+                     +------------+-----------+
             |                                                |
             +----+     Provider IP as identifier    +--------+
                  |                                  +
           +------+------+                    +------+------+
           + Hyperswitch +        ....        + Hyperswitch +
           +------+------+                    +------+------+
                  |     OSLO Messaging (RabbitMQ)    |
                  +----------------+-----------------+
                                   |
                               +---+----+
                               | Jacket |
                               +--------+


The First implementation supports AWS EC2 and Openstack providers.


hypernet agent less Neutron Extension
=====================================

This extension defined two new entities:
   - agentlessport: This entity defines the parameters of neutron port than can be connected by OpenVPN

      - id: the agentlessport id, i.e. the provider port or network interface id
      - port_id: The neutron port id
      - flavor: The network flavor (0G, 1G or 10G)
      - device_id: the device id that belong the port
      - index: 0, 1 or 2, the index of the NIC in the VM 
      - user_data: read only, the user data to used for Provider VM creation

   - hyperswitch: This entity represents a Provider virtual machine that acts as a OpenVPN server and are a part of the Openstack mesh

      - id: the provider VM id or name
      - flavor: The network flavor (0G, 1G or 10G)
      - device_id: The Nova Virtual Machine id connected to this hyperswitch
      - tenant_id: The tenant identifier of the Virtual machine connected to this hyperswitch
      - instance_id: the Provider instance identifier (read only)
      - instance_type: The provider instance type (read only)
      - private_ip: The provider Hyperswitch primary IP
      - mgnt_ip: The Hyperswitch Management IP
      - data_ip: The Hyperswitch Data IP
      - vms_ip_0: The Hyperswitch Server VPN for index 0 IP
      - vms_ip_1: The Hyperswitch Server VPN for index 1 IP
      - vms_ip_2: The Hyperswitch Server VPN for index 2 IP


These 2 entities are not kept in the Neutron DB but only as provider entities:
  - Interface Network TAGS and VM TAGs for Hyperswitch VM in AWS
  - Openstack Port fields and VM Metadata for Hyperswitch VM in Openstack

Management APIs
***************

Create agentlessport
--------------------

It Must be call during the jacket nova driver Plug vif:
  - Create a provider port/Network Interface
  - Create an hyperswitch if not exist for this agent less port according the the default hyperswitch flavor (0G, 1G or 10G) and level (per vm or tenant):

     - if a flavor is given as a parameter, this flavor is used to create the hyperswitch if created
     - if a device_id is given as a parameter, the level is per vm for this device

Return (id, port_id, user_data)

List agentlessports
-------------------
Get agentlessport entities members according to names, port_ids, device_ids, private_ips, tenant_ids and/or indexes.
Only filter by name (identifier) and and private_ip should have implementation for each cloud provider. Other filters are optionals.

Show agentlessport
-------------------
Get agentlessport entity members from identifier.

Delete agentlessport
--------------------
Remove the agentlessport entity from identifier:
   - Remove the provider port/Network Interface
   - Remove the hyperswitch VM if this the last agentlessport that can be connected to the level:
      - For vm level, it always remove
      - For tenant level, it's only remove for the last agentlessport.

Create hyperswitchs
-------------------
Create an extra hyperswitch VM for a tenant or for a dedicated device (VM).

List hyperswitchs
-----------------
Get hyperswitchs entities members according to names, ids, tenant_ids and/or device_ids.

Show hyperswitch
----------------
Get hyperswitch entity members from identifier.

Delete hyperswitch
------------------
Remove an hyperswitch entity from identifier: remove the extra hyperswitch VM.

Configuration
*************

Options List::
  +------------------------+------------+-------------------+--------------------------------------+
  | options                | Type       | Default Value     | Description                          |
  +========================+============+===================+======================================+
  | provider               | string     | openstack         | Provider: aws, openstack or null     |
  +------------------------+------------+-------------------+--------------------------------------+
  | level                  | string     | tenant            | Level: tenant or vm.                 |
  +------------------------+------------+-------------------+--------------------------------------+
  | mgnt_network           | string     |                   | Provider Mgnt network id or name.    |
  +------------------------+------------+-------------------+--------------------------------------+
  | mgnt_security_group    | string     |                   | Provider Mgnt network SG id or name. |
  +------------------------+------------+-------------------+--------------------------------------+
  | data_network           | string     |                   | Provider Data network id or name.    |
  +------------------------+------------+-------------------+--------------------------------------+
  | data_security_group    | string     |                   | Provider Data network SG id or name. |
  +------------------------+------------+-------------------+--------------------------------------+
  | vms_networks           | list       |                   | Provider VMs networks id/name list   |
  |                        |            |                   | for not automatic network creation.  |
  |                        |            |                   | in place of vms_cidr                 |
  +------------------------+------------+-------------------+--------------------------------------+
  | vms_cidr               | list       | [172.31.192.0/20, | CIDRs for OPenVPN VMs NICs.          |
  |                        |            | 172.31.208.0/20,  |                                      |
  |                        |            | 172.31.224.0/20]  |                                      |
  +------------------------+------------+-------------------+--------------------------------------+
  | hs_sg_name             | string     | hs_sg_vms_123456  | Provider SG name for VPN Server NICS |
  +------------------------+------------+-------------------+--------------------------------------+
  | vm_sg_name             | string     | vm_sg_vms_123456  | Provider SG name for agent less NICs |
  +------------------------+------------+-------------------+--------------------------------------+
  | default_flavor         | string     | 1G                | Default network flavor hyperswitch   |
  |                        |            |                   | creation: 0G, 1G or 10G              |
  +------------------------+------------+-------------------+--------------------------------------+
  | hs_flavor_map          | dict       |                   | HyperSwitch flavor Map               |
  +------------------------+------------+-------------------+--------------------------------------+
 
AWS specific::
  +------------------------+------------+-------------------+--------------------------------------+
  | options                | Type       | Default Value     | Description                          |
  +========================+============+===================+======================================+
  | aws_vpc                | string     |                   | AWS VPC id.                          |
  +------------------------+------------+-------------------+--------------------------------------+
  | aws_access_key_id      | string     |                   | AWS Access Key Id.                   |
  +------------------------+------------+-------------------+--------------------------------------+
  | aws_secret_access_key  | string     |                   | AWS Secret Access Key.               |
  +------------------------+------------+-------------------+--------------------------------------+
  | aws_region_name        | string     |                   | AWS Region Name.                     |
  +------------------------+------------+-------------------+--------------------------------------+

Openstack specific::
  +------------------------+------------+----------------+--------------------------------------+
  | options                | Type       | Default Value  | Description                          |
  +========================+============+================+======================================+
  |                        |            |                |                                      |
  +------------------------+------------+----------------+--------------------------------------+


Code Design
***********

Class Diagram
-------------

hyperswitch extension::

  +-------------+                        +---------------------+
  | Hyperswitch +------------------------+ ExtensionDescriptor |
  +-------------+                        +---------------------+


  +-------------------+                 +-----------------------+
  | HyperswitchPlugin +-----------------+ HyperswitchPluginBase |
  +-------------------+                 +-----------------------+


  +-------------+               
  | AWSProvider +---------------+
  +-------------+               |         +- --------------+
                                +---------+ ProviderDriver |
                                |         +----------------+
  +-------------------+         |
  | OpenStackProvider +---------+
  +-------------------+

ProviderDriver Interface
------------------------

...

  class ProviderDriver(object):
    def get_sgs():
        return None, None
    def get_vms_subnet():
        return []
    def get_hyperswitch_host_name(hybrid_cloud_device_id=None, hybrid_cloud_tenant_id=None):
        pass
    def launch_hyperswitch(user_data, flavor, net_list, hybrid_cloud_device_id=None, hybrid_cloud_tenant_id=None):
        pass
    def get_hyperswitchs(names=None, hyperswitch_ids=None, device_ids=None, tenant_ids=None):
        return []
    def start_hyperswitchs(hyperswitchs):
        pass
    def delete_hyperswitch(hyperswitch_id):
        pass
    def create_network_interface(port_id, device_id, tenant_id, index, subnet, security_group):
        pass
    def get_network_interfaces(names=None, port_ids=None, device_ids=None, private_ips=None, tenant_ids=None, indexes=None):
        pass

...


HyperSwitch Agents
==================

Modules
*******
The hyperswitch VM includes 4 agents to implements the neutron functionalities.

Neutron Openvswitch agent
-------------------------
Standard Neutron Openvswitch agent that should match with the cascaded openstack version for L2/SG functionalities.

Neutron L3 Agent
----------------
Standard Neutron L3 agent in DVR mode that should match with the cascaded openstack version for DVR router deployment.

Neutron Metadata Agent
----------------------
Standard Neutron Metadata agent necessary on each compute node for DVR deployment that should match with the cascaded openstack version.

Hyperswitch Local Controller Agent
-----------------------------------
TODO: Local Controller for br-vpn diagram::
   -

TODO: Lazy plug vif diagram and flow diagram::
   -



