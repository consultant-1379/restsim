#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 18.02
# Purpose       :  Script to setup scanner and ENM time sync
# Jira No       :
# Gerrit Link   :
# Description   : Script to setup scanner and ENM time sync
# Date          :  08/12/2017
# Last Modified :  mathur.priyank@tcs.com
####################################################


CONFIGFILE=/netsim/netsim_cfg
BIN_DIR=/netsim_users/pms/bin
CREATE_SCANNER=0
TIME_SYNC=0

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

while getopts  "st" flag
do
    case "$flag" in

        s) CREATE_SCANNER=1;;
        t) TIME_SYNC=1;;
		
    esac
done

if [ ${CREATE_SCANNER} -eq 1 ] ; then
    for SERVER in $SERVERS ; do
        echo "INFO: Create scanners"
        ${BIN_DIR}/scanners.sh -d -a create -s ${SERVER}
        if [ $? -ne 0 ] ; then
            echo "ERROR: scanners.sh failed"
            exit 1
        fi
	done	
fi

if [ ${TIME_SYNC} -eq 1 ] ; then
    for SERVER in $SERVERS ; do
        echo "INFO: Timesync"
        ${BIN_DIR}/timesync -d -s ${SERVER}
	done
fi
