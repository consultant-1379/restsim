#!/bin/bash

#################################################################################### 
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.12
# Purpose       :  The purpose of this script to setup the required configurations for GenStats
# Jira No       :
# Gerrit Link   :
# Description   :  Adding backward compatibility for set_tmpfs
# Date          :  24/07/2017
# Last Modified :  Tom McGreal
####################################################

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

GENSTATS_CONSOLELOGS="/netsim/genstats/logs/rollout_console/genstats_pm_setup_stats_recordings.log"
CONFIGFILE=/netsim/netsim_cfg
NETSIM_LOG_DIR=/netsim_users/pms/logs

if [ ! -r ${CONFIGFILE} ] ; then
    log "ERROR: Cannot find ${CONFIGFILE}"
    log "ERROR: Cannot find ${CONFIGFILE}" > $GENSTATS_CONSOLELOGS
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

if [ ! "${SET_BANDWIDTH_LIMITING}" = "OFF" ] ; then
        log "INFO: Apply bandwidth limiting"
        
        #/usr/bin/rsh -l root ${SERVERS} ${BIN_DIR}/limitbw -n -c > ${NETSIM_LOG_DIR}/limitbw.log
        echo shroot | su root -c "${BIN_DIR}/limitbw -n -c > ${NETSIM_LOG_DIR}/limitbw.log"
        
        #/usr/bin/rsh -l root ${SERVERS} ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log
        echo shroot | su root -c "${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log"
        
        if [ $? -ne 0 ] ; then
            log "ERROR: limitbw failed"
            log "ERROR: limitbw failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
        
        #/usr/bin/rsh -l root ${SERVERS} "crontab -l | grep -v limitbw > /tmp/new_crontab"
        echo shroot | su root -c "crontab -l | grep -v limitbw > /tmp/new_crontab"
        
        #/usr/bin/rsh -l root ${SERVERS} "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        
        #/usr/bin/rsh -l root ${SERVERS} "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        
        #/usr/bin/rsh -l root ${SERVERS} "echo \"@reboot ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"@reboot ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        
        #/usr/bin/rsh -l root ${SERVERS} "crontab /tmp/new_crontab"
        echo shroot | su root -c "crontab /tmp/new_crontab"
fi

