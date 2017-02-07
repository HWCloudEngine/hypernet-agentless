#!/bin/bash

rm -rf ./build
rm -rf /usr/local/lib/python2.7/dist-packages/hypernet*
rm -rf /usr/local/bin/hyperswitch*

ovs-vsctl del-br br-vpn
ovs-vsctl del-br br-int
ovs-vsctl del-br br-ex
ovs-vsctl add-br br-ex

python ./setup.py clean
python ./setup.py build
python ./setup.py install

# init conf
rm -f /etc/init/hyperswitch*
cp -r ./etc/agent/init/* /etc/init

# etc hyperswitch conf
rm -rf /etc/hyperswitch
cp -r ./etc/agent/hyperswitch /etc

# templates
rm -rf `find /etc -name "*.tmpl"`
cp ./etc/agent/neutron/neutron.conf.tmpl /etc/neutron
cp ./etc/agent/neutron/metadata_agent.ini.tmpl /etc/neutron
cp ./etc/agent/neutron/plugins/ml2/ml2_conf.ini.tmpl /etc/neutron/plugins/ml2
cp ./etc/hosts.tmpl /etc

# var folder
rm -rf /var/log/hyperswitch
mkdir /var/log/hyperswitch

rm -f /etc/hyperswitch/hyperswitch.conf
rm -f /etc/neutron/neutron.conf
rm -f /etc/neutron/metadata_agent.ini
rm -f /etc/neutron/plugins/ml2/openvswitch_agent.ini
