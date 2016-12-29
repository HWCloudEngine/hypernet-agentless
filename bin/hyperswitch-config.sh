#!/bin/bash
set -x

CONF_DIRS="/etc/neutron /etc/hyperswitch"
PARAMS="rabbit_userid rabbit_hosts rabbit_password host local_ip network_mngt_interface network_data_interface network_vms_interface"

function get_user_data {
    # get user data from 169.254.169.254
    curl http://169.254.169.254/latest/user-data/ > /tmp/user-data-1111
    source /tmp/user-data-1111
}

# try to read for user data from 169.254.169.254
get_user_data

export local_ip=`ip -o -4 a | grep ${network_data_interface} | awk -e '{print $4}' | cut -f1 -d'/'`

# replace the tmpl values
sed_command=""
for p in $PARAMS; do
   val=${!p}
   val=${val//\//\\/}
   val=${val//\&/\\&}
   val=${val//$'\n'/}
   sed_command=`echo "s/##$p##/${val}/g;$sed_command"`
done;
echo $sed_command

for d in $CONF_DIRS; do
   for f_tmpl in `find $d -name "*.tmpl"`; do
      f="${f_tmpl%.*}"
      sed $f_tmpl -e "$sed_command" > $f
   done;
done;

echo $host > /etc/hostname
hostname $host
grep -v 127.0.0.1 /etc/hosts > /tmp/hosts.bk2
echo '127.0.0.1 localhost '$host > /tmp/hosts.bk1
cat /tmp/hosts.bk1 /tmp/hosts.bk2 > /etc/hosts