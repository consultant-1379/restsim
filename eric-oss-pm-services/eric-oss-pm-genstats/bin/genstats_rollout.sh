#!/bin/sh
#################################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.10
# Purpose       :  Script is responsible for GenStats Rollout Process using docker.
# Jira No       :  NSS-12488
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2390323
# Description   :  Adding change for GenStats Rollout Process using docker.
# Date          :  06/12/2017
# Last Modified :  g.multani@tcs.com
####################################################
spawn ssh netsim@netsim
expect "Are you sure you want to continue connecting (yes/no)? "
send "yes\r"
expect "Password: "
send "netsim\r"
expect "netsim@netsim:~> "
send "echo '.show started' | /netsim/inst/netsim_shell > /tmp/.showstartednodes.txt\r"
expect "netsim@netsim:~> "
send "cat /tmp/.showstartednodes.txt > /tmp/showstartednodes.txt\r"
expect "netsim@netsim:~> "
send "echo '.show netypes' | /netsim/inst/netsim_shell > /tmp/.netypes.txt\r"
expect "netsim@netsim:~> "
send "cat /tmp/.netypes.txt > /tmp/netypes.txt\r"
expect "netsim@netsim:~> "
send "su - root\r"
expect "Password: "
send "shroot\r"
expect "netsim:~ #"
send "bash /netsim_users/pms/bin/remove_stop_nodes.sh\r"
expect "netsim:~ #"
send "su - netsim\r"
expect "netsim@netsim:~> "
send "mkdir /netsim_users/pms/logs /netsim_users/pms/etc\r"
expect "netsim@netsim:~> "
send "touch /netsim_users/pms/etc/eutrancellfdd_list.txt\r"
expect "netsim@netsim:~> "
send "python /netsim_users/auto_deploy/bin/getSimulationData.py\r"
expect "netsim@netsim:~> "
send "python /netsim_users/auto_deploy/bin/netsim_cfg_gen_docker.py\r"
expect "netsim@netsim:~> "
send "cp /tmp/netsim /netsim/netsim_cfg\r"
expect "netsim@netsim:~> "
send "/netsim_users/pms/bin/GetEutranData.py\r"
expect "netsim@netsim:~> "
send "sed -i '7,9 s/^/#/' /netsim_users/pms/bin/timesync\r"
expect "netsim@netsim:~> "
send "sed -i '11 s/^/#/' /netsim_users/pms/bin/timesync\r"
expect "netsim@netsim:~> "
send "/netsim_users/pms/bin/pm_setup_stats_recordings.sh -c /netsim/netsim_cfg\r"
expect "Are you sure you want to continue connecting (yes/no)? "
send "yes\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "Password: "
send "shroot\r"
expect "netsim@netsim:~> "
send "exit\r"
