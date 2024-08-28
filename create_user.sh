#!/bin/bash

groupadd flsusers
mkdir -p /ericsson/pmic/
useradd -d /ericsson/pmic/ -g flsusers flsuser1
echo flsuser1:flspass@12 | chpasswd

cd /ericsson/

chown -R root:root pmic/
chmod 777 pmic
cd pmic

sed -i -e "s/#Port/Port/g" /etc/ssh/sshd_config
sed -i -e "s/#SyslogFacility/SyslogFacility/g" /etc/ssh/sshd_config
sed -i -e "s/#LogLevel/LogLevel/g" /etc/ssh/sshd_config

sed -i 's/^#\?ChallengeResponseAuthentication .*/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#GSSAPIAuthentication no/GSSAPIAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#GSSAPICleanupCredentials yes/GSSAPICleanupCredentials no/' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin yes/#PermitRootLogin yes/' /etc/ssh/sshd_config

sed -i 's/^#HostKey \/etc\/ssh\/ssh_host_rsa_key/HostKey \/etc\/ssh\/ssh_host_rsa_key/' /etc/ssh/sshd_config
sed -i 's/^#HostKey \/etc\/ssh\/ssh_host_ecdsa_key/HostKey \/etc\/ssh\/ssh_host_ecdsa_key/' /etc/ssh/sshd_config
sed -i 's/^#HostKey \/etc\/ssh\/ssh_host_ed25519_key/HostKey \/etc\/ssh\/ssh_host_ed25519_key/' /etc/ssh/sshd_config

if [[ $LOGGING_LEVEL == "DEBUG" ]]; then
    sed -i -e "s|/var/log/secure|/netsim_users/pms/logs/secure|g" /etc/rsyslog.conf
    sed -i -e "s|/var/log/messages|/netsim_users/pms/logs/mesages|g" /etc/rsyslog.conf
fi

sudo systemctl restart rsyslog
sudo systemctl restart sshd

rm -rf /run/nologin
