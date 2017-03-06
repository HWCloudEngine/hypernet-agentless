#!/bin/bash
set -x

# based on ubuntu 14.04.03

# manual configuration for AWS:
#   Network configuration:
#      eth0 is the management network: dhcp or manual with default gw update
#      eth1 is the data network: dhcp or manual without gw update
#      eth2 is the vms network: dhcp or manual without gw update

#   sysctl configuration
#      set in /etc/sysctl.conf
#         - net.ipv4.conf.all.rp_filter 0
#         - net.ipv4.conf.default.rp_filter 0
#      sysctl -p

# deactivate no wanted services
systemctl disable firewalld
systemctl stop firewalld
systemctl disable NetworkManager
systemctl stop NetworkManager
systemctl enable network
systemctl start network

# install the nova/neutron packages
yum install -y centos-release-openstack-mitaka
yum install -y epel-release
yum update -y
yum install -y openstack-neutron-openvswitch
yum install -y bridge-utils python-ryu
yum install -y openvpn easy-rsa

systemctl enable neutron-openvswitch-agent.service
systemctl enable openvswitch.service
service openvswitch start

ovs-vsctl --may-exist add-br br-ex

yum install -y git
git clone https://github.com/Hybrid-Cloud/hypernet-agentless.git

FROM_DIR="/root/hypernet-agentless/"
cd $FROM_DIR

# hyper agent python packages
python ./setup.py install

# TODO: move the binary and configuration installation to the setup.py
# binaries
bin_files='hyperswitch-config.sh'
for f in $bin_files
do
    rm -f /usr/bin/$f
    cp $FROM_DIR/bin/$f /usr/bin
done

# init conf
rm -f /usr/lib/systemd/system/hyperswitch*
cp -r $FROM_DIR/etc/agent/systemd/* /usr/lib/systemd/system/

systemctl daemon-reload

systemctl enable hyperswitch-cleanup.service
systemctl enable hyperswitch-config.service
systemctl enable hyperswitch.service

# etc hyperswitch conf
rm -rf /etc/hyperswitch
cp -r $FROM_DIR/etc/agent/hyperswitch /etc

# neutron template
rm -rf `find /etc/neutron -name "*.tmpl"`
cp $FROM_DIR/etc/agent/neutron/dvr_compute_agent.ini.tmpl /etc/neutron
cp $FROM_DIR/etc/agent/neutron/dhcp_agent.ini.tmpl /etc/neutron
cp $FROM_DIR/etc/agent/neutron/plugins/openvswitch/ovs_neutron_plugin.ini.tmpl /etc/neutron/plugins/openvswitch

# var folder
rm -rf /var/log/hyperswitch
mkdir /var/log/hyperswitch

# TODO: openvpn certificates creation: CA, server and one client
# etc openswan conf
rm -rf /etc/openswan
cp -r $FROM_DIR/etc/agent/openswan /etc