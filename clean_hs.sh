#!/bin/bash

rm -rf /opt/hyperswitch
mkdir /opt/hyperswitch

cp -r . /opt/hyperswitch

ovs-vsctl del-br br-vpn
ovs-vsctl del-br br-eth0
ovs-vsctl del-br br-eth1
ovs-vsctl del-br br-eth2
ovs-vsctl del-br br-eth3
ovs-vsctl del-br br-eth4
ovs-vsctl del-br br-eth5
ovs-vsctl del-br br-int
ovs-vsctl del-br br-ex
ovs-vsctl add-br br-ex

# templates
rm -rf `find /etc -name "*.tmpl"`
cp ./etc/agent/neutron/neutron.conf.tmpl /etc/neutron
cp ./etc/agent/neutron/metadata_agent.ini.tmpl /etc/neutron
cp ./etc/agent/neutron/plugins/ml2/ml2_conf.ini.tmpl /etc/neutron/plugins/ml2
cp ./etc/agent/hosts.tmpl /etc

# init conf
rm -f /etc/init/hyperswitch*
cp -r ./etc/agent/init/* /etc/init

# etc hyperswitch conf
rm -rf /etc/hyperswitch
cp -r ./etc/agent/hyperswitch /etc

# var folder
rm -rf /var/log/hyperswitch
mkdir /var/log/hyperswitch

# clean current configuration
rm -f /etc/hyperswitch/hyperswitch.conf
rm -f /etc/neutron/neutron.conf
rm -f /etc/neutron/metadata_agent.ini
rm -f /etc/neutron/plugins/ml2/openvswitch_agent.ini
