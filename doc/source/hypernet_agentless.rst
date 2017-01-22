==================
HyperNet Agentless
==================

Hyper Network Background
========================

Hybrid cloud architecture is based on an openstack managment instance (called jacket, Embedded Openstack or Cascaded) that translates the openstack APIs and entities to the provider APIs and entities.

Utilizing openstack neutron the solution implements Hyper Network, Hyper Port, and Hyper Security Group as cascaded neutron entities.

The Virtual Machines, Provider Networks and Provider Security groups are provided by the underline cloud provider (AWS or openstack).

The requirements for an agent less solution is to connect a custumers workload using native provider's Virtual Machine with minimal changes in this virtual machine; i.e.: using standard software packages in the customer workload.
Any changes to the hyper network implemented by the cascaded neutron functionalities (L2: Hyper IP and Network, L3: Hyper Subnet, Hyper SG etc...) are preferred than changes in the VM customer workload.

The challenge with that kind of changes, is that the cloud provider does not provide all neutron functionalities, which should be implemented by agents and extra provider's virtual machine.

Data Path Solution
==================

The presented solution for the data path is based on a standard VPN client installed in the Provider VM. This VPN connects to a VPN server installed on dedicated Provider's Virtual Machines. These Provider Virtual Machines are called 'hyperswith' (which provides the entry point to the Hyper Network) and provides all the neutron functionalities. The VPN client receives the Hyper IP with DHCP protocol on the VPN termination and replace the network routes the the hyper network one.

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


Control Path Solution
=====================

The Control Path implementation is based on a neutron extension, a plugin in the jacket and an agent installed in the hyperswitch VM. The hypernet agentless neutron plugin implements: 
   - hyperswitch APIs to manage the extra provider virtual machine (hyperswitches)
   - agentlessport APIs to define a hyper port as an agent less port
   - Messaging supplementary API for the hyperswitch agent control communication.

Control Path - High Level Modules::

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


Deep-depth diagram::


                 +---------------------------+
                 |       Windows VM          |
                 |                           |
                 |   +----------------+      |
                 |   | OpenVPN client |      |
                 |   +----------+-----+      |
                 +--------------|------------+
                                |
                                |
               +----------------|----------------------------------------------------------+
               | Hyperswitch    |                                                          |
               |     +----------|--------+                                                 |
               |     | br-vpn   |        |                                                 |
               |     |       +--+---+    |   +----------------+                            |
               |     |       | ethX |    +---+ HS Controller  |                            |
               |     |       +--+---+    |   +--------------+-+                            |
               |     +----------|--------+                  |                              |
               |                |                           |                              |
               |      +---------+-------+                   |                              |
               |      | OpenVPN Server  |                   |                              |
               |      +---------+-------+                   |                              |
               |                |                           |   +-------------------+      |
               |             +--+---+                       | +-+ neutron ovs agent |      |
               |             | tap  | - SG iptables         | | +-------------------+      |
               |             +--+---+                       | |                            |
               |                |                           | | +-------------------+      |
               |     +----------|--------+                  | +-+ neutron l3 agent  |      |
               |     | br-int   |        |                  | | +-------------------+      |
               |     |       +--+---+    |                  | |                            |
               |     |       | qvo  |    |                  | | +------------------------+ |
               |     |       +------+    |  +-----------+   | +-+ neutron metadata agent | |
               |     |                   |  |qbr        |   | | +------------------------+ |
               |     |       +------+    |  | +------+  |   | |                            |
               |     |       | xxxx +---------+ xxxx |  |   | |                            |
               |     |       +------+    |  | +------+  |   | |                            |
               |     |       +------+    |  | +------+  |   | |                            |
               |     |       | xxxx +---------+ xxxx |  |   | |                            |
               |     |       +------+    |  | +------+  |   | |                            |
               |     +-------------------+  +-----------+   | |                            | 
               +--------------------------------------------|-|----------------------------+
                                                            | |
               +--------------------------------------------|-|-----+
               | Jacket                                     | |     |
               |  +-----------------------------------------|-+---+ |
               |  | Neutron Server               +----------+---+ | |
               |  |                              | HS Agent API | | |
               |  |                              +--------------+ | |
               |  |   +--------------+                            | |
               |  |   | HS Plugin    |                            | |
               |  |   +----+---------+                            | |
               |  +--------|--------------------------------------+ |
               +-----------|----------------------------------------+
                           |
                           | Rest agentlessport/hyperswtich APIs
                           |
               +-----------+-------------+
               | extended neutron client |
               +-------------------------+

The First implementation supports AWS EC2 and Openstack providers.


Hypernet Agentless Neutron Extension
====================================

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


These 2 entities are not kept in the neutron DB but only as provider entities:
  - Interface Network TAGS and VM TAGs for Hyperswitch VM in AWS
  - Openstack Port fields and VM Metadata for Hyperswitch VM in Openstack

Management APIs
***************

Create agentlessport
--------------------

It Must be called on the jacket nova driver "Plug vif" call:
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
  +----------------------+------------+---------------+--------------------------------------------+
  | options              | Type       | Default Value | Description                                |
  +======================+============+===============+============================================+
  | fs_username          | string     |               | openstack provider login user name         |
  +----------------------+------------+---------------+--------------------------------------------+
  | fs_password          | string     |               | openstack provider login password          |
  +----------------------+------------+---------------+--------------------------------------------+
  | fs_tenant_id         | string     |               | openstack provider login tenant id         |
  +----------------------+------------+---------------+--------------------------------------------+
  | fs_auth_url          | string     |               | openstack provider auth URL (keystone URL) |
  +----------------------+------------+---------------+--------------------------------------------+
  | fs_availability_zone | string     |               | availability zone for Hyperswitch creation |
  +----------------------+------------+---------------+--------------------------------------------+


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
----------------------------------

TODO: Lazy plug vif diagram and flow diagram::
   -



