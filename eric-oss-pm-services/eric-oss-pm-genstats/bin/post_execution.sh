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
# Version no    :  NSS 18.03
# Purpose       :  The purpose of this script to setup the required configurations for GenStats
# Jira No       :
# Gerrit Link   :
# Description   :  Adding backward compatibility for set_tmpfs
# Date          :  24/07/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################


BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

GENSTATS_CONSOLELOGS="/netsim/genstats/logs/rollout_console/genstats_pm_setup_stats_recordings.log"

CONFIGFILE=/netsim/netsim_cfg
CREATE_SCANNERS=1
BULK_PM_ENABLED="False"

while getopts  "s:c:nb:" flag
do
    case "$flag" in

        c) CONFIGFILE="$OPTARG";;
        s) SERVER_LIST="$OPTARG";;
        n) CREATE_SCANNERS=0;;
		b) BULK_PM_ENABLED="$OPTARG";;

        *) printf "Usage: %s < -c configfile > <-s serverlist> <-n>\n" $0
           exit 1;;
    esac
done

# clean old unmounted simulations from netsim_dbdir
/netsim_users/pms/bin/cleanNETSimDBsimDir.py

if [ ! -r ${CONFIGFILE} ] ; then
    log "ERROR: Cannot find ${CONFIGFILE}"
    log "ERROR: Cannot find ${CONFIGFILE}" > $GENSTATS_CONSOLELOGS
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

checkPMDIR
if [ $? -ne 0 ] ; then
    log "ERROR: PMDIR not set correctly"
    log "ERROR: PMDIR not set correctly" >> $GENSTATS_CONSOLELOGS
    exit 1
fi

NETSIM_PMS_DIR=/netsim_users/pms
NETSIM_ETC_DIR=${NETSIM_PMS_DIR}/etc
NETSIM_BIN_DIR=${NETSIM_PMS_DIR}/bin
NETSIM_LOG_DIR=${NETSIM_PMS_DIR}/logs

HAS_WRAN=0
HAS_LTE=0
for SERVER in $SERVERS ; do
    SERVER_SIM_LIST=`getSimListForServer ${SERVER}`
    for SERVER_SIM in ${SERVER_SIM_LIST} ; do
        SIM_TYPE=`getSimType ${SERVER_SIM}`
        if [ "${SIM_TYPE}" = "WRAN" ] ; then
            HAS_WRAN=1
        elif [ "${SIM_TYPE}" = "LTE" ] ; then
            HAS_LTE=1
        fi
    done
done

if [ ${HAS_WRAN} -eq 1 ] ; then
    UTRANCELL_LIST=${PMDIR}/utrancell_list.txt
    if [ ! -r ${UTRANCELL_LIST} ] ; then
        log "ERROR: Cannot find UtranCell file ${UTRANCELL_LIST}"
        log "ERROR: Cannot find UtranCell file ${UTRANCELL_LIST}" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi
fi


if [ ${HAS_LTE} -eq 1 ] ; then
    EUTRANCELL_LIST=${PMDIR}/eutrancellfdd_list.txt
    if [ ! -r ${EUTRANCELL_LIST} ] ; then
        log "ERROR: Cannot find EUtranCell file ${EUTRANCELL_LIST}"
        log "ERROR: Cannot find EUtranCell file ${EUTRANCELL_LIST}" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi
fi

for SERVER in $SERVERS ; do
    log "INFO: ${SERVER}"

    log "INFO: Removing /tmp/netypes.txt, /tmp/showstarted.txt and /netsim_users/.count"
    #/usr/bin/rsh -l root ${SERVER} "rm -rf  /tmp/netypes.txt; rm -rf /tmp/showstartednodes.txt; rm -rf /tmp/nodetypes.txt; rm -rf /tmp/nodetypes.tmp.txt; rm -rf /netsim_users/.count;"
	echo shroot | su root -c "rm -rf  /tmp/netypes.txt; rm -rf /tmp/showstartednodes.txt; rm -rf /tmp/nodetypes.txt; rm -rf /tmp/nodetypes.tmp.txt; rm -rf /netsim_users/.count;"
	
    log "INFO: Copy netsim_cfg"
    /bin/cp ${CONFIGFILE} /netsim/netsim_cfg

    log "INFO:  Creating directories"
    for DIR in ${NETSIM_LOG_DIR} ${NETSIM_ETC_DIR} ; do
        #/usr/bin/rsh -l root ${SERVER} "if [ ! -d ${DIR} ] ; then mkdir ${DIR} ; fi ; chown -R netsim:netsim ${DIR}; find ${DIR} -type f -exec chmod 644 {} \;"
        echo shroot | su root -c "if [ ! -d ${DIR} ] ; then mkdir ${DIR} ; fi ; chown -R netsim:netsim ${DIR}; find ${DIR} -type f -exec chmod 644 {} \;"
    done

    #if [ "${TYPE}" != "NSS" ]; then
    #    log "INFO: settmpfs"
    #    /usr/bin/rsh -l netsim ${SERVER} ${NETSIM_BIN_DIR}/settmpfsWrapper.sh
    #   if [ $? -ne 0 ] ; then
    #       log "ERROR: settmpfs failed"
    #       log "ERROR: settmpfs failed" >> $GENSTATS_CONSOLELOGS
    #       exit 1
    #   fi
    #fi

    log "INFO: Fetching started node details"
    `echo '.show started' | /netsim/inst/netsim_pipe > /tmp/.showstartednodes.txt`
    `echo '.show started' | /netsim/inst/netsim_pipe > /tmp/showstartednodes.txt`

    if [ "${TYPE}" = "NSS" ] && [[ $(echo "${NSS_RELEASE} < 17.12" | bc) -eq 1 ]]; then
        log "INFO: settmpfs"
        #/usr/bin/rsh -l netsim ${SERVER} ${NETSIM_BIN_DIR}/settmpfs.sh
        `${NETSIM_BIN_DIR}/settmpfs.sh`
        if [ $? -ne 0 ] ; then
            log "ERROR: settmpfs failed"
            log "ERROR: settmpfs failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi


    if [ "${TYPE}" = "NSS" ]; then
        log "INFO: Deleting the node folders from /pms_tmpfs that are not started"
        bash /netsim_users/pms/bin/remove_stop_nodes.sh
    fi

    log "INFO:  Fetching file location"
    python /netsim_users/auto_deploy/bin/fetchFileLocation.py

    log "INFO: Start fetching radio node site location."
    SITE_LOCATION_SCRIPT="/netsim_users/auto_deploy/bin/getNodeSiteLocation.py"
    python ${SITE_LOCATION_SCRIPT}

    log "INFO: createTempFsMountForNodes.sh"
    #/usr/bin/rsh -l root ${SERVER} ${NETSIM_BIN_DIR}/createTempFsMountForNodes.sh
    echo shroot | su root -c "${NETSIM_BIN_DIR}/createTempFsMountForNodes.sh"
    if [ $? -ne 0 ] ; then
        log "ERROR: createTempFsMountForNodes.sh failed"
        log "ERROR: createTempFsMountForNodes.sh failed" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi

    log "INFO: Copy cell lists"
    if [ ${HAS_WRAN} -eq 1 ] ; then
        /bin/cp ${UTRANCELL_LIST} ${NETSIM_ETC_DIR}/utrancell_list.txt
        if [ $? -ne 0 ] ; then
            log "ERROR: Copy failed"
            log "ERROR: Copy failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi
    if [ ${HAS_LTE} -eq 1 ] ; then
        /bin/cp ${EUTRANCELL_LIST} ${NETSIM_ETC_DIR}/eutrancellfdd_list.txt
        if [ $? -ne 0 ] ; then
            log "ERROR: Copy failed"
            log "ERROR: Copy failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi

    log "INFO: Stats"
    ${BIN_DIR}/pm_statistcs.sh -s ${SERVER} -c ${CONFIGFILE} -b ${BULK_PM_ENABLED}
    if [ $? -ne 0 ] ; then
        log "ERROR: pm_statistcs failed"
        log "ERROR: pm_statistcs failed" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi

    log "INFO: setup UETR_CTR"
    if [[ "${TYPE}" != "NSS" ]] && [[ "${TYPE}" != "NRM1.2" ]]; then
        python /netsim_users/auto_deploy/bin/CreateMmeRefCfg.py
    fi
    ${BIN_DIR}/pm_recordings_UETR_CTR.sh -s ${SERVER} -c ${CONFIGFILE}
    if [ $? -ne 0 ] ; then
        log "ERROR: pm_recordings_UETR_CTR failed"
        log "ERROR: pm_recordings_UETR_CTR failed" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi

    log "INFO: setup GPEH"
    if [[ "${TYPE}" != "NRM1.2" ]]; then
        ${BIN_DIR}/setup_GPEH.sh -s ${SERVER} -c ${CONFIGFILE} -v 1
        if [ $? -ne 0 ] ; then
            log "ERROR: setup_GPEH failed"
            log "ERROR: setup_GPEH failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi

    #setting up periodic HC cron
    periodic_first_HC="/tmp/.first_periodic_hc_exec"

    if [[ -f ${periodic_first_HC} ]]; then
        rm -f ${periodic_first_HC}
    fi
    
    #/usr/bin/rsh -l netsim ${SERVER} "crontab -l | egrep -v '^# |genstat_report.sh' > /tmp/periodic_hc_crontab"
    `crontab -l | egrep -v '^# |genstat_report.sh' > /tmp/periodic_hc_crontab`

    phc_check_first=$(cat /netsim/netsim_cfg | grep PERIODIC_HC_INTERVAL | grep -v '#' | wc -l)
    phc_check_second=$(cat /tmp/${SERVER} | grep PERIODIC_HC_INTERVAL | grep -v '#' | wc -l)
    
    if [[ "${TYPE}" != "NSS" ]]; then
        if [[ ${phc_check_first} -eq 0 ]]; then
            #/usr/bin/rsh -l netsim ${SERVER} "echo '' >> /netsim/netsim_cfg"
            `echo '' >> /netsim/netsim_cfg`
            
            #/usr/bin/rsh -l netsim ${SERVER} "echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /netsim/netsim_cfg"
            `echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /netsim/netsim_cfg`
        fi
        if [[ ${phc_check_second} -eq 0 ]]; then 
            #/usr/bin/rsh -l netsim ${SERVER} "echo '' >> /tmp/${SERVER}"
            `echo '' >> /tmp/${SERVER}`
            
            #/usr/bin/rsh -l netsim ${SERVER} "echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /tmp/${SERVER}"
            `echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /tmp/${SERVER}`
        fi
        log "INFO: Setting up periodic Health Check cron entry"
        #/usr/bin/rsh -l netsim ${SERVER} "echo \"* * * * * /netsim_users/hc/bin/genstat_report.sh -p true >> ${NETSIM_LOG_DIR}/periodic_healthcheck.log 2>&1\" >> /tmp/periodic_hc_crontab"
        echo "* * * * * /netsim_users/hc/bin/genstat_report.sh -p true >> ${NETSIM_LOG_DIR}/periodic_healthcheck.log 2>&1" >> /tmp/periodic_hc_crontab
    else
        if [[ ${phc_check_first} -ne 0 ]] || [[ ${phc_check_second} -ne 0 ]]; then
            log "ERROR: PERIODIC_HC_INTERVAL should not be defined in /netsim/netsim_cfg or in /tmp/${SERVER} file for deployment ${TYPE}."
        fi
    fi

    #/usr/bin/rsh -l netsim ${SERVER} "crontab /tmp/periodic_hc_crontab"
    `crontab /tmp/periodic_hc_crontab`

done

