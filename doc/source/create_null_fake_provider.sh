
export OS_USERNAME=admin
export OS_PASSWORD=stack
export OS_TENANT_NAME=admin
export OS_PROJECT_NAME=admin
keystone tenant-create  --name fake-provider-tenant --enabled true
keystone user-create --name fake --tenant fake-provider-tenant --enabled true --pass fake

export OS_USERNAME=fake
export OS_PASSWORD=fake
export OS_TENANT_NAME=fake-provider-tenant
export OS_PROJECT_NAME=fake-provider-tenant
neutron net-create provider_net
neutron subnet-create --disable-dhcp --ip-version 4 provider_net 172.20.10.0/24



export OS_USERNAME=demo
export OS_PASSWORD=stack
export OS_TENANT_NAME=demo
export OS_PROJECT_NAME=demo
neutron port-list

# create fake neutron port
export OS_USERNAME=fake
export OS_PASSWORD=fake
export OS_TENANT_NAME=fake-provider-tenant
export OS_PROJECT_NAME=fake-provider-tenant
neutron port-create --device-id 4d8631ee-a0bc-43ac-af19-13b237c9a5a7 --fixed-ip subnet_id=e491e233-7d17-4e51-a958-25dbce260e8a,ip_address=172.20.10.20 --name 6585a2d7-e6e9-4150-bcbe-e55afaca5b89 provider_net
