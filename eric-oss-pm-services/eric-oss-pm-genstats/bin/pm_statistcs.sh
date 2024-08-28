#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 22.15
# Purpose       :  Script is responsible to add crontab entry for STATS as well as EVENTS ROP generation for all Nodes types supported by PMS
# Jira No       :  NSS-40727
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/13317646/
# Description   :  Added logs rotation support 
# Date          :  14/09/2022
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################

#This script is responsible to add crontab entry for STATS as well as EVENTS ROP generation as per configuration in netsim_cfg file.

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

CONFIGFILE=/netsim/netsim_cfg
while getopts  "s:c:b:" flag
do
    case "$flag" in

    c) CONFIGFILE="$OPTARG";;
    s) SERVER_LIST="$OPTARG";;
    b) BULK_PM_ENABLED="$OPTARG";;
    *) printf "Usage: %s < -c configfile > <-s serverlist>\n" $0
           exit 1;;
    esac
done
if [ ! -r ${CONFIGFILE} ] ; then
    echo "ERROR: Cannot find ${CONFIGFILE}"
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi



# STATS_WORKLOAD_LIST variable is must as this defines the rop configuration if not present then log
# message and exit the program execution.
if [ -z "${STATS_WORKLOAD_LIST}" ] ; then
    log "Variable STATS_WORKLOAD_LIST not found or not set in config file hence STATS rollout cannot be done"
    exit 1
fi


NETSIM_BIN_DIR=/netsim_users/pms/bin
NETSIM_LOG_DIR=/netsim_users/pms/logs
NETSIM_DBDIR=/netsim/netsim_dbdir/simdir/netsim/netsimdir
SIM_DATA_FILE=/netsim/genstats/tmp/sim_data.txt
HOST=`hostname`
HOST_NAME=`echo $HOST`
FLEX_SIM_LIST_NSS=($(cat /netsim/genstats/tmp/sim_info.txt | egrep -i "SGSN|R6274|R6675|R6672|R6673|R6371|R6471-1|R6471-2|R6273|CSCF|SBG|MTAS|VBGF|MRF|WCG|DSC|VSAPC" | egrep -v "TSP|SBG-IS" | awk -F":" '{ print $2 }' | sort -u))
FLEX_SIM_LIST_NRM=($(cat /netsim/genstats/tmp/sim_info.txt | egrep -i "MTAS|DSC" | egrep -v "TSP" | awk -F":" '{ print $2 }' | sort -u))
ML_OUTDOOR_SIM_LIST=($(ls ${NETSIM_DBDIR} | egrep "ML.*6352|ML.*6351|MLPT2020|FrontHaul-6392|Switch6391"))
LOCAL_OFFSET=`date +%z`
OFFSET_HOUR=`date +%z | cut -c 2-3`
OFFSET_MIN=`date +%z | cut -c 4-5`

FRONTHAUL_CHECK=False
echo $PLAYBACK_SIM_LIST | grep "FrontHaul" > /dev/null
if [[ $? == 0 ]];then
    FRONTHAUL_CHECK=True
fi

# storing default IFS
OLDIFS=$IFS
if [[ "${TYPE}" = "NRM"* ]]; then	
    # get an array of only R6672, R6675 and SPITFIRE for sim_data.txt file
    IFS=$'\n'
    ROUTER_NODE_TYPE_R6672_R6675_SPITFIRE_ARRAY=($(cat $SIM_DATA_FILE | egrep "R6672|R6675|SPITFIRE"))
    set IFS
    
    for line in ${ROUTER_NODE_TYPE_R6672_R6675_SPITFIRE_ARRAY[*]}; do
        if [[ ${line}  == *"CORE01"* ]] || [[ ${line}  == *"Transport"* ]] ; then
           ROUTER_NODE_TYPE_R6672_R6675_SPITFIRE=($(echo "$line" | egrep -i 'R6672|R6675|SPITFIRE' | awk -F" " '{print $6}'))		
           ROUNTER_NODE_NAME=($(echo "$line" | awk -F" " '{print $4}'))
           ROUTER_SIM_NAME=($(echo "$line" | awk -F" " '{print $2}'))
           break
        fi
    done
fi

# restoring default IFS
IFS=$OLDIFS

PLAYBACK_FLEX_SIM_LIST=''
echo $PLAYBACK_SIM_LIST | egrep "EPG-OI" > /dev/null
if [[ $? == 0 ]];then
    PLAYBACK_FLEX_SIM_LIST='vEPG-OI EPG-OI'
fi

for SERVER in $SERVERS ; do
    log "INFO: Templates"
    ${BIN_DIR}/rollout_xml_templates.sh -c ${CONFIGFILE} -s ${SERVER}
    if [ $? -ne 0 ] ;then
    log "ERROR: Template rollout failed for ${SERVER}"
    exit 1
    fi

    #  STATS_WORKLOAD_LIST=<ROP Interval>:<NE_TYPE/ALL[,NE_TYPE ..]>
    log "INFO: Crontab"
    crontab -l | egrep -v "^# |genStats|flexrop.sh|rmPmFiles|getStartedNodes|removeLogFiles.py|startPlaybacker.sh|updateMiniLinkOutdoorFile.py|update_ml_templates.py|ml_pm_service.py" > /tmp/_new_crontab


    if [ "${HOST_NAME}" = "netsim" ]; then
        echo "4,9,14,19,24,29,34,39,44,49,54,59 * * * * ${NETSIM_BIN_DIR}/getStartedNodes" >> /tmp/_new_crontab
    elif [ "${TYPE}" = "NSS" ]; then
        echo "14,29,44,59 * * * * ${NETSIM_BIN_DIR}/getStartedNodes" >> /tmp/_new_crontab
    fi

    ml_pids=($(ps -eaf | grep -i "ml_pm_service.py" | grep -v "grep" | awk -F' ' '{print $2}' | sed 's/ //g'))
    for ml_pid in ${ml_pids[@]}; do
        if [[ ! -z ${ml_pid} ]]; then
            kill -9 ${ml_pid}
        fi
    done
    rm -rf /pms_tmpfs/xml_step/minilink_templates/ > /dev/null 2>&1

    if [[ ${#ML_OUTDOOR_SIM_LIST[@]} -ne 0 ]];then
        log "INFO: ML Outdoor Simulations found."
        echo "12,27,42,57 * * * * python /netsim_users/auto_deploy/bin/update_ml_templates.py >> /netsim_users/pms/logs/minilink_precook_data.log 2>&1" >> /tmp/_new_crontab
        echo "*/15 * * * * python /netsim_users/auto_deploy/bin/ml_pm_service.py" >> /tmp/_new_crontab

        log "INFO: Executing MiniLink Template Updater for first time."
        python /netsim_users/auto_deploy/bin/update_ml_templates.py firstexecution
        log "INFO: MiniLink Template Updater completed."

        log "INFO: Executing MiniLink Template Updater for second time."
        python /netsim_users/auto_deploy/bin/update_ml_templates.py
        log "INFO: MiniLink Template Updater completed."
    fi

    echo "58 23 1,16 * * /netsim_users/pms/bin/logs_rotation.sh" >> /tmp/_new_crontab

    echo "*/5 * * * * /netsim_users/pms/bin/flexrop.sh" >> /tmp/_new_crontab

    if [[ "${TYPE}" = "NSS" ]]; then
        # Default 24h ROP without DST
        if ! [[ -z ${FLEX_SIM_LIST_NSS} ]];then
            NODE_LIST=${FLEX_SIM_LIST_NSS[@]}
            for node in ${NODE_LIST[@]};do

                /netsim_users/pms/bin/configFlexRop.sh -l ${node} -r 1440 -c 'ADD'
            done
        fi
        if ! [[ -z ${PLAYBACK_FLEX_SIM_LIST} ]];then
            NODE_LIST=${PLAYBACK_FLEX_SIM_LIST[@]}
            for node in ${NODE_LIST[@]};do

                /netsim_users/pms/bin/configFlexRop.sh -l ${node} -r 1440 -c 'ADD'
            done
        fi
    elif [[ "${TYPE}" = "NRM"* ]]; then
        if ! [[ -z ${FLEX_SIM_LIST_NRM} ]]; then
            NODE_LIST=${FLEX_SIM_LIST_NRM[@]}
            for node in ${NODE_LIST[@]};do

                /netsim_users/pms/bin/configFlexRop.sh -l ${node} -r 1440 -c 'ADD'
            done
            echo "* * * * *  /netsim_users/pms/bin/genStats -r 1 -l \"${FLEX_SIM_LIST_NRM[*]}\"  >> /netsim_users/pms/logs/genStats_1min.log 2>&1" >> /tmp/_new_crontab
        fi
        if [[ ${FRONTHAUL_CHECK} = True ]];then
           FRONTHAUL_NODES='FrontHaul-6020 FrontHaul-6080'
           NODE_LIST=${FRONTHAUL_NODES[@]}
           for node in ${NODE_LIST[@]};do

                /netsim_users/pms/bin/configFlexRop.sh -l ${node} -r 1440 -c 'ADD'
           done
        fi
        if [[ ${ROUNTER_NODE_NAME} ]] && [[ ${ROUTER_NODE_TYPE_R6672_R6675_SPITFIRE} ]]; then
            echo "* * * * *  /netsim_users/pms/bin/genStats -r 1 -l '${ROUTER_NODE_TYPE_R6672_R6675_SPITFIRE}'  >> ${NETSIM_LOG_DIR[0]}/genStats_1min.log 2>&1" >> /tmp/_new_crontab
            python /netsim_users/auto_deploy/bin/generateSelectiveNeConf.py --sim ${ROUTER_SIM_NAME} --rop 1 --count 40
        fi

    fi


    if [ "${BULK_PM_ENABLED}" != "True" ]; then
    for STATS_WORKLOAD in $STATS_WORKLOAD_LIST; do
        ROP_PERIOD=`echo ${STATS_WORKLOAD} | awk -F: '{print $1}'`
        NE_TYPES=`echo ${STATS_WORKLOAD} | awk -F: '{print $2}'`

        #Added HOUR_FIELD to support for 24hrs ROP generation.
        case "${ROP_PERIOD}" in
             1) MINUTE_FIELD="*";HOUR_FIELD="*";;
             5) MINUTE_FIELD="0,5,10,15,20,25,30,35,40,45,50,55";HOUR_FIELD="*";;
            15) MINUTE_FIELD="0,15,30,45";HOUR_FIELD="*";;
            60) MINUTE_FIELD="0";HOUR_FIELD="*";;
            1440) MINUTE_FIELD="0";HOUR_FIELD="0";;
             *) printf " Invalid ROP interval : ${ROP_PERIOD} \n" $0
             exit 1;;
        esac

        if [ ${NE_TYPES} = "ALL" ] ; then
            echo "${MINUTE_FIELD} ${HOUR_FIELD} * * * ${NETSIM_BIN_DIR}/genStats -r ${ROP_PERIOD} >> ${NETSIM_LOG_DIR}/genStats_${ROP_PERIOD}min.log 2>&1" >> /tmp/_new_crontab

            echo "${MINUTE_FIELD} ${HOUR_FIELD} * * * ${NETSIM_BIN_DIR}/startPlaybacker.sh -r ${ROP_PERIOD} >> ${NETSIM_LOG_DIR}/playbacker_${ROP_PERIOD}min.log 2>&1" >> /tmp/_new_crontab
        else

            NE_TYPES=$(echo $NE_TYPES | sed 's/,/ /g')
            CMD="${MINUTE_FIELD} ${HOUR_FIELD} * * * ${NETSIM_BIN_DIR}/genStats -r ${ROP_PERIOD} -l \\\"${NE_TYPES}\\\""
            echo "${CMD}  >> ${NETSIM_LOG_DIR}/genStats_${ROP_PERIOD}min.log 2>&1" >> /tmp/_new_crontab

            CMD_Playbacker="${MINUTE_FIELD} ${HOUR_FIELD} * * * ${NETSIM_BIN_DIR}/startPlaybacker.sh -r ${ROP_PERIOD} -l \\\"${NE_TYPES}\\\""
            echo "${CMD_Playbacker}  >> ${NETSIM_LOG_DIR}/playbacker_${ROP_PERIOD}min.log 2>&1" >> /tmp/_new_crontab
        fi
    done

	echo "0 * * * * ${NETSIM_BIN_DIR}/rmPmFiles >> ${NETSIM_LOG_DIR}/rmFiles.log 2>&1" >> /tmp/_new_crontab

    fi

    `crontab /tmp/_new_crontab`

done

if [ ! -z "${LOG_FILE_RETENTION}" ] ; then

   if [ "${LOG_FILE_RETENTION}" -gt "23" ] ; then
        REMOVAL_TIME_IN_DAYS="*/"$((${LOG_FILE_RETENTION}/24))
        REMOVAL_TIME_IN_HOURS="*"
   else
        REMOVAL_TIME_IN_DAYS="*"
        REMOVAL_TIME_IN_HOURS="*/"${LOG_FILE_RETENTION}
   fi
   echo "0 ${REMOVAL_TIME_IN_HOURS} ${REMOVAL_TIME_IN_DAYS} * * ${NETSIM_BIN_DIR}/removeLogFiles.py" >> /tmp/_new_crontab

   `crontab /tmp/_new_crontab`
fi

