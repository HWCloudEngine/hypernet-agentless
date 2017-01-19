#!/bin/bash

function configure_hyperswitch_plugin {
    sudo cp $HYPERSWITCH_DIR/etc/server/neutron/hyperswitch_plugin.ini $HYPERSWITCH_CONF_FILE
}


if [[ "$1" == "stack" && "$2" == "install" ]]; then
    setup_develop $DEST/hypernet-agentless
elif [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        _neutron_service_plugin_class_add $HYPERSWITCH_PLUGIN
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_hyperswitch_plugin
    echo_summary "Configuring hypernet-agentless"
    if [ "$HYPERSWITCH_PROVIDER" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch provider
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch provider $HYPERSWITCH_PROVIDER
    fi
    if [ "$HYPERSWITCH_LEVEL" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch level
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch level $HYPERSWITCH_LEVEL
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch mgnt_network
    if [ "$HYPERSWITCH_MGNT_NETWORK" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch mgnt_network $HYPERSWITCH_MGNT_NETWORK
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch mgnt_security_group
    if [ "$HYPERSWITCH_MGNT_SECURITY_GROUP" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch mgnt_security_group $HYPERSWITCH_MGNT_SECURITY_GROUP
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch data_network
    if [ "$HYPERSWITCH_DATA_NETWORK" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch data_network $HYPERSWITCH_DATA_NETWORK
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch data_security_group
    if [ "$HYPERSWITCH_DATA_SECURITY_GROUP" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch data_security_group $HYPERSWITCH_DATA_SECURITY_GROUP
    fi
    if [ "$HYPERSWITCH_VMS_NETWORK" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch vms_networks
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch vms_networks $HYPERSWITCH_VMS_NETWORK
    fi
    if [ "$HYPERSWITCH_VMS_CIDR" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch vms_cidr
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch vms_cidr $HYPERSWITCH_VMS_CIDR
    fi
    if [ "$HYPERSWITCH_HS_SG_NAME" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch hs_sg_name
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch hs_sg_name $HYPERSWITCH_HS_SG_NAME
    fi
    if [ "$HYPERSWITCH_VM_SG_NAME" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch vm_sg_name
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch vm_sg_name $HYPERSWITCH_VM_SG_NAME
    fi
    if [ "$HYPERSWITCH_HS_DEFAULT_FLAVOR" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch hs_default_flavor
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch hs_default_flavor $HYPERSWITCH_HS_DEFAULT_FLAVOR
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch hs_flavor_map
    if [ "$HYPERSWITCH_HS_FLAVOR_MAP" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch hs_flavor_map $HYPERSWITCH_HS_FLAVOR_MAP
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch aws_access_key_id
    if [ "$HYPERSWITCH_AWS_ACCESS_KEY" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch aws_access_key_id $HYPERSWITCH_AWS_ACCESS_KEY
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch aws_secret_access_key
    if [ "$HYPERSWITCH_AWS_SECRET_ACCESS_KEY" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch aws_secret_access_key $HYPERSWITCH_AWS_SECRET_ACCESS_KEY
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch aws_region_name
    if [ "$HYPERSWITCH_AWS_REGION_NAME" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch aws_region_name $HYPERSWITCH_AWS_REGION_NAME
    fi
    inicomment $HYPERSWITCH_CONF_FILE hyperswitch aws_vpc
    if [ "$HYPERSWITCH_AWS_VPC" ]; then
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch aws_vpc $HYPERSWITCH_AWS_VPC
    fi
    if [ "$HYPERSWITCH_FS_USERNAME" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch fs_username
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch fs_username $HYPERSWITCH_FS_USERNAME
    fi
    if [ "$HYPERSWITCH_FS_PASSWORD" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch fs_password
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch fs_password $HYPERSWITCH_FS_PASSWORD
    fi
    if [ "$HYPERSWITCH_FS_TENANT_ID" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch fs_tenant_id
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch fs_tenant_id $HYPERSWITCH_FS_TENANT_ID
    fi
    if [ "$HYPERSWITCH_FS_AUTH_URL" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch fs_auth_url
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch fs_auth_url $HYPERSWITCH_FS_AUTH_URL
    fi
    if [ "$HYPERSWITCH_FS_AVAILABILITY_ZONE" ]; then
        inicomment $HYPERSWITCH_CONF_FILE hyperswitch fs_availability_zone
        iniadd $HYPERSWITCH_CONF_FILE hyperswitch fs_availability_zone $HYPERSWITCH_FS_AVAILABILITY_ZONE
    fi
elif [[ "$1" == "stack" && "$2" == "post-extra" ]]; then
    # no-op
    :
fi

if [[ "$1" == "unstack" ]]; then
    # no-op
    :
fi
