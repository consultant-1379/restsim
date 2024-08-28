#!/bin/bash
################################################################################
# COPYRIGHT Ericsson 2016
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.5
# Purpose       :  Script is responsible to sftp all transport node templates to ENM application.
# Jira No       :  NSS-9902
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2099354/
# Description   :  SFTP  all transport nodes template to ENM application.
# Date          :  16/02/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################
EXPECT=/usr/bin/expect
SFTP=/usr/bin/sftp

_user_=$1
shift
_host_=$1
shift
_pw_=$1
shift
line=$*
  IFS=','
  array=($line)
for index in "${!array[@]}"
do
commands[$index]={${array[index]}}
done
IFS="$oIFS"
echo "commands $commands"

$EXPECT << EOF >> /dev/null 2>&1
spawn $SFTP ${_user_}@${_host_}
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r"}
"Password:" {send "$_pw_\r"}
"sftp>" {send "\r"}
}
expect {
"Password:" {send "$_pw_\r"}
"sftp>" {send "\r"}
}
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r"}
"password:" {send "$_pw_\r"}
"sftp>" {send "\r"}
}
expect {
"password:" {send "$_pw_\r"}
"sftp>" {send "\r"}
}
foreach cmd "${commands[@]}" {
        expect "sftp>"
        send "\$cmd\r"
    }
expect "sftp>"
send "quit\r"
expect eof
EOF
