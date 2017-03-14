
keystone service-create --name hypernet --type hypernet --description "OpenStack Hypernet"

keystone endpoint-create \
--service-id $(keystone service-list | awk '/ hypernet / {print $2}') \
--publicurl http://10.10.128.71:8333 \
--adminurl http://10.10.128.71:8333 \
--internalurl http://10.10.128.71:8333 \
--region regionOne

keystone endpoint-create \
--service-id $(keystone service-list | awk '/ hypernet / {print $2}') \
--publicurl http://controller:8333 \
--adminurl http://controller:8333 \
--internalurl http://controller:8333 \
--region regionOne



