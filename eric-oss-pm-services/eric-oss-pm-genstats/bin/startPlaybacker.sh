#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2021
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 22.05
# Purpose       :  The purpose of this script to call STATS and EVENTS playbacker framework as per configuration mentioned in /netsim_users/pms/bin/playback_cfg file and generate PM files for STATS and EVENTS respectively.
# Jira No       :  NSS-35517
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/11675757/
# Description   :  Adding 20mb file support for SCEF in MD_1
# Date          :  29/01/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

#@script: startPlaybacker.sh
#@description:This script is responsible for initialisation of all one time constant variables,getting started nodes from netsim box,dividing input files like events and stats respectively into batches and calling respective stats and events sandbox script for dumping respective stats and events file into each started node as per netsim directory structure.


######### Main Function ############

umask 000

INSTALL_DIR_NAME=`dirname $0`
INSTALL_DIR=`cd ${INSTALL_DIR_NAME} ; pwd`
LOG_PATH="/netsim_users/pms/logs"
LOG_DATE=`date "+%Y_%m_%d_%H:%M:%S"`
SANDBOX_DIR="/netsim_users/pms/sandbox_templates/"
PMS_TMPFS_GEN_NODES="ECEE EPG-OI vEPG-OI WMG-OI vWMG-OI gNodeBRadio SBG-IS FrontHaul-6020 FrontHaul-6080 vCU-UP vCU-CP vAFG ADP SCEF"
EPG_OI_TYPE_DST_NODES="EPG-OI vEPG-OI WMG-OI vWMG-OI ADP vDU vCU-UP vCU-CP"
NSS_ONLY_NE_TYPES="ECEE ADP vWMG-OI WMG-OI vAFG"
DO_SUPPORTED_NE_TYPES="vWMG-OI vEPG-OI vAFG VCUDB"
CC_DIR="/tmp/${ROP_PERIOD_MIN}/playbacker_CC"

if [ ! -d ${CC_DIR} ] ; then
    mkdir -p ${CC_DIR}
fi

find ${CC_DIR} -type f -exec rm {} \;

if [ ! -d ${LOG_PATH}/.logs ] ; then
    mkdir -p ${LOG_PATH}/.logs
fi

LOG=${LOG_PATH}/.logs/log_backup_${LOG_DATE}

# Need to source this first to override some vars (e.g. PMDIR)
if [ -r /netsim/netsim_cfg ] ; then
    . /netsim/netsim_cfg > /dev/null 2>&1
fi

#Importing Sandbox_cfg file
if [ -r /${INSTALL_DIR}/playback_cfg ] ; then
    . /${INSTALL_DIR}/playback_cfg
fi

#Importing common functions
if [ -r /${INSTALL_DIR}/functions ] ; then
    . /${INSTALL_DIR}/functions
fi

#Check whether playback list is empty
if [[ -z ${PLAYBACK_SIM_LIST} ]];then
    log "INFO: Playback List is empty.Exiting Process."
    exit 1
fi

ROP_PERIOD_MIN=15
STATS_MAX_CONCURRENT=3

while getopts  "r:l:z:j:" flag
do
    case "$flag" in
        j) MY_EPOCH="$OPTARG";;
        r) ROP_PERIOD_MIN="$OPTARG";;
        l) NE_TYPE_LIST="$OPTARG";;
        z) EXEC_FROM_HC="$OPTARG";;
        *) printf "Usage: %s [ -r rop interval in mins ] [ -l ne types <NE1:NE2> ] \n" $0
           exit 1;;
    esac
done

if [ -z ${ROP_PERIOD_MIN} ] ; then
    ROP_PERIOD_MIN=15
fi

STEP_DIR="/pms_tmpfs/xml_step/sandbox_templates/"

############################# SET ROP TIMINIGS #############################
# Generate Epoch Seconds (UTC always)
current_epoch=$(date +%s)

if [[ ! -z ${MY_EPOCH} ]]; then
    current_epoch=${MY_EPOCH}
fi

ROP_PERIOD_SEC=$((${ROP_PERIOD_MIN}*60))

if [[ ${EXEC_FROM_HC} == "YES" ]]; then
    start_epoch=$(($((${current_epoch}/60))*60))
elif [[ ${ROP_PERIOD_SEC} -gt 900 ]];then
    start_epoch=$(($((${current_epoch}/900))*900))
else
    start_epoch=$(($((${current_epoch}/${ROP_PERIOD_SEC}))*${ROP_PERIOD_SEC}))
fi
end_epoch=$((${start_epoch}+${ROP_PERIOD_SEC}))
epoch_rop_folder="${start_epoch}_${end_epoch}"

# UTC TIMESTAMP
DATE=$(date -u -d @${start_epoch} +'%Y%m%d')
ROP_START_TIME=$(date -u -d @${start_epoch} +'%H%M')
ROP_END_DATE_UTC=$(date -u -d @${end_epoch} +'%Y%m%d')
ROP_END_TIME=$(date -u -d @${end_epoch} +'%H%M')
STARTDATE_UTC="${DATE}${ROP_START_TIME}"

# LOCAL TIMESTAMP
DATE_LOCAL=$(date -d @${start_epoch} +'%Y%m%d')
ROP_START_TIME_LOCAL=$(date -d @${start_epoch} +'%H%M')
ROP_LOCAL_OFFSET=$(date -d @${start_epoch} +'%z')
ROP_END_DATE_LOCAL=$(date -d @${end_epoch} +'%Y%m%d')
ROP_END_TIME_LOCAL=$(date -d @${end_epoch} +'%H%M')
ROP_LOCAL_END_OFFSET=$(date -d @${end_epoch} +'%z')

#FrontHaul and ORAN LOCAL END TIME Handling
FH_ORAN_ROP_END_TIME_LOCAL=$(date -d @${end_epoch} +'%H%M')
FH_ORAN_ROP_LOCAL_END_OFFSET=$(date -d @${end_epoch} +'%z')
EPG_OI_ROP_START_TIME_LOCAL=$(date -d @${start_epoch} +'%H%M')
EPG_OI_ROP_START_OFFSET_LOCAL=$(date -d @${start_epoch} +'%z')
# End time offset and Entime will be handled here for FH nodes and ORAN nodes for DST change between ROP
if [[ ${ROP_LOCAL_OFFSET} != ${ROP_LOCAL_END_OFFSET} ]];then
   FH_ORAN_UTC_END_TIME=$(date -u -d @${end_epoch} +'%H%M')
   OFFSET_TYPE=$(echo ${ROP_LOCAL_OFFSET} | cut -c 1)
   OFFSET_HOUR=$(echo ${ROP_LOCAL_OFFSET} | cut -c 2,3)
   OFFSET_MIN=$(echo ${ROP_LOCAL_OFFSET} | cut -c 4,5)
   EPG_OI_UTC_START_TIME=$(date -u -d @${start_epoch} +'%H%M')
   EPG_OI_OFFSET_TYPE=$(echo ${ROP_LOCAL_END_OFFSET} | cut -c 1)
   EPG_OI_OFFSET_HOUR=$(echo ${ROP_LOCAL_END_OFFSET} | cut -c 2,3)
   EPG_OI_OFFSET_MIN=$(echo ${ROP_LOCAL_END_OFFSET} | cut -c 4,5)

   if [[ ${OFFSET_TYPE} == "+" ]];then
       FH_ORAN_ROP_END_TIME_LOCAL=$(date -u -d "${FH_ORAN_UTC_END_TIME} +${OFFSET_HOUR} hour $OFFSET_MIN minutes " +"%H%M")
       EPG_OI_ROP_START_TIME_LOCAL=$(date -u -d "${EPG_OI_UTC_START_TIME} +${EPG_OI_OFFSET_HOUR} hour $EPG_OI_OFFSET_MIN minutes " +"%H%M")
   else
       FH_ORAN_ROP_END_TIME_LOCAL=$(date -u -d "${FH_ORAN_UTC_END_TIME} -${OFFSET_HOUR} hour ${OFFSET_MIN} minutes " +"%H%M")
       EPG_OI_ROP_START_TIME_LOCAL=$(date -u -d "${EPG_OI_UTC_START_TIME} -${EPG_OI_OFFSET_HOUR} hour $EPG_OI_OFFSET_MIN minutes " +"%H%M")
   fi
   FH_ORAN_ROP_LOCAL_END_OFFSET=${ROP_LOCAL_OFFSET}
   EPG_OI_ROP_START_OFFSET_LOCAL=${ROP_LOCAL_END_OFFSET}
fi

ZERO=00

#This method will create TIMESTAMP for provide Timezone
createTimeStampWithConfigTZ(){
    TIMEZONE=${1}
    DATE_REF_TZ=$(TZ=${TIMEZONE} date -d @${start_epoch} +'%Y%m%d')
    ROP_START_TIME_TZ=$(TZ=${TIMEZONE} date -d @${start_epoch} +'%H%M')
    ROP_TZ_OFFSET=$(TZ=${TIMEZONE} date -d @${start_epoch} +'%z')
    ROP_END_DATE_TZ=$(TZ=${TIMEZONE} date -d @${end_epoch} +'%Y%m%d')
    ROP_END_TIME_TZ=$(TZ=${TIMEZONE} date -d @${end_epoch} +'%H%M')
    ROP_TZ_END_OFFSET=$(TZ=${TIMEZONE} date -d @${end_epoch} +'%z')

    if [[ ${ROP_TZ_OFFSET} != ${ROP_TZ_END_OFFSET} ]];then
       ORAN_TZ_END_TIME=$(TZ=${TIMEZONE} date -u -d @${end_epoch} +'%H%M')
       OFFSET_TYPE=$(echo ${ROP_TZ_OFFSET} | cut -c 1)
       OFFSET_HOUR=$(echo ${ROP_TZ_OFFSET} | cut -c 2,3)
       OFFSET_MIN=$(echo ${ROP_TZ_OFFSET} | cut -c 4,5)

       if [[ ${OFFSET_TYPE} == "+" ]];then
          ROP_END_TIME_TZ=$(date -u -d "${ORAN_TZ_END_TIME} +${OFFSET_HOUR} hour $OFFSET_MIN minutes " +"%H%M")
       else
          ROP_END_TIME_TZ=$(date -u -d "${ORAN_TZ_END_TIME} -${OFFSET_HOUR} hour ${OFFSET_MIN} minutes " +"%H%M")
       fi
    fi
}

############################################################################

UNIQUE_ID=1001

FILE_beginTime=$(date -u -d @${start_epoch} +'%Y-%m-%dT%H:%M:00%:z')
FILE_endTime=$(date -u -d @${end_epoch} +'%Y-%m-%dT%H:%M:00%:z')
TSP_MPID_TIME_START_DATETIME="${DATE}${ROP_START_TIME}"

TWENTY_FOUR_HOUR_SIMS="FrontHaul-6020 FrontHaul-6080"

CPP_START_TIME_STAMP=$(date -d @${start_epoch} +'%Y-%m-%dT%H:%M:00%:z')
CPP_END_TIME_STAMP=$(date -d @${end_epoch} +'%Y-%m-%dT%H:%M:00%:z')
TSP_START_TIME_STAMP=$(date -d @${start_epoch} +'%Y%m%d%H%M00.0%z')
TSP_END_TIME_STAMP=$(date -d @${end_epoch} +'%Y%m%d%H%M00.0%z')
system_time=$(date -d @${start_epoch} +'%H:%M')

if [[ ${ROP_PERIOD_MIN} == 15 ]]; then
    dur="900"
elif [[ ${ROP_PERIOD_MIN} == 1 ]]; then
    dur="60"
else
    dur="86400"
fi

echo -e "CPP;${CPP_START_TIME_STAMP};${CPP_END_TIME_STAMP}\nTSP;${TSP_START_TIME_STAMP};${TSP_END_TIME_STAMP}\nBSP;${FILE_beginTime};${FILE_endTime}" > "/netsim_users/pms/etc/.playback_node_timestamp_${ROP_PERIOD_MIN}_min"

log "Start ${STARTDATE_UTC}"

DATE_REF=""

for SIM_NAME in ${PLAYBACK_SIM_LIST}; do
 
    if grep -q ${SIM_NAME} "/tmp/showstartednodes.txt"; then

        for NE in ${NE_TYPE_LIST}; do

            if [[ "${SIM_NAME}" == *${NE}* ]]; then
                NUM_RUNNING=`ls ${CC_DIR} | wc -l | awk '{print $1}'`
                while [ ${NUM_RUNNING} -ge ${STATS_MAX_CONCURRENT} ] ; do
                    sleep 1
                    NUM_RUNNING=`ls ${CC_DIR} | wc -l | awk '{print $1}'`
                done
                LOCK_FILE=${CC_DIR}/${STARTDATE_UTC}.${SIM_NAME}
                touch ${LOCK_FILE}
                log "Processing SIM : ${SIM_NAME}"
                #Filtering SIM NAME (replacing - to _ in SIM NAME)
                old_NE=${NE}
                NE=`echo ${NE} | sed s/-/_/g`
                #For STATS file generation
                stats="$NE"_GENRATE_STATS
                if [[ ${!stats} == "YES" ]] ; then
                    stats_file_format="${NE}"_STATS_OUTPUT_FILE_FORMAT
                    stats_output_type="${NE}"_STATS_OUTPUT_TYPE
                    stats_input_location="${NE}"_STATS_INPUT_LOCATION
                    script="startStatsPlayback.sh"
                    stats_TZ="$NE"_STATS_OUTPUT_TZ
                    stats_update_TZ="${NE}"_STATS_UPDATE_TZ
                    append_path="$NE"_PM_FileLocation

                    #Use tmpfs location as input location
                    echo ${PMS_TMPFS_GEN_NODES} | grep -w ${NE/_/-} >> /dev/null
                    if [[ $? -eq 0 ]];then
                       if [[ ! -d ${STEP_DIR}/${NE}/ ]];then
                          mkdir -p ${STEP_DIR}/${NE}/
                          cp -r ${!stats_input_location}/* ${STEP_DIR}/${NE}/
                       fi
                    stats_input_location=${STEP_DIR}/${NE}/
                    fi

                    if [[ ${NE} == *EPG_OI* ]] || [[ -z ${!append_path} ]];then
                        append_path="$NE"_STATS_APPEND_PATH
                    fi

                    if [[ ${!stats_TZ} == "LOCAL" ]] ; then
                        DATE_REF=${DATE_LOCAL}
                        if [[ ${NE} == "SBG_IS" ]] ; then
                            ROP_START_TIME_STATS=${ROP_START_TIME_LOCAL}${ZERO}${ROP_LOCAL_OFFSET}
                            ROP_END_TIME_STATS=${ROP_END_TIME_LOCAL}${ZERO}${ROP_LOCAL_END_OFFSET}
                            ROP_END_DATE=${ROP_END_DATE_LOCAL}
                        else
                            ROP_START_TIME_STATS=${ROP_START_TIME_LOCAL}${ROP_LOCAL_OFFSET}
                            ROP_END_TIME_STATS=${ROP_END_TIME_LOCAL}${ROP_LOCAL_END_OFFSET}
                            ROP_END_DATE=${ROP_END_DATE_LOCAL}
                            if [[ ${NE} == *"FrontHaul"* ]] ; then
                                ROP_END_TIME_STATS=${FH_ORAN_ROP_END_TIME_LOCAL}${FH_ORAN_ROP_LOCAL_END_OFFSET}
                            elif [[ ${NE} == "ECEE" ]] ; then
                                ROP_END_TIME_STATS=${ROP_END_TIME_LOCAL}
                                ROP_END_DATE=${ROP_END_DATE_LOCAL: -4}
                            else
                                echo ${EPG_OI_TYPE_DST_NODES} | grep -w ${NE/_/-} >> /dev/null
                                if [[ $? -eq 0 ]];then
                                   if [[ $ROP_PERIOD_MIN == 1440 ]];then
                                       ROP_START_TIME_STATS=${ZERO}${ZERO}${EPG_OI_ROP_START_OFFSET_LOCAL}
                                       ROP_END_TIME_STATS=${ZERO}${ZERO}${ROP_LOCAL_END_OFFSET}
                                   else
                                       ROP_START_TIME_STATS=${EPG_OI_ROP_START_TIME_LOCAL}${EPG_OI_ROP_START_OFFSET_LOCAL}
                                   fi
                                fi 
                            fi
                        fi
                    else
                        DATE_REF=${DATE}
                        ROP_END_DATE=${ROP_END_DATE_UTC}
                        if [[ ${NE} == "SBG_IS" ]] ; then
                            ROP_START_TIME_STATS=${ROP_START_TIME}${ZERO}
                            ROP_END_TIME_STATS=${ROP_END_TIME}${ZERO}
                        else
                            ROP_START_TIME_STATS=${ROP_START_TIME}
                            ROP_END_TIME_STATS=${ROP_END_TIME}
                        fi
                    fi

                    if [[ ${NE} == "SBG_IS" ]] ; then
                        /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${UNIQUE_ID}" &

                    elif [[ ${NE} == "HSS_FE_TSP" ]] || [[ ${NE} == "MTAS_TSP" ]] || [[ ${NE} == "CSCF_TSP" ]] || [[ ${NE} == "SAPC_TSP" ]] || [[ ${NE} == *"EIR_FE"* ]] || [[ ${NE} == *"VCUDB"* ]] ; then
                        MEASUREMENT_JOB_NAME="${NE}"_MEASUREMENT_JOB_NAME
                        stats_input_location=${!stats_input_location}
                        for FULL_JOB_NAME in ${!MEASUREMENT_JOB_NAME}; do
                            JOB_NAME=`echo $FULL_JOB_NAME | cut -d":" -f1`
                            if [[ ${NE} == *"EIR_FE"* ]]; then
                                if [[ ${TYPE} != "NSS" ]]; then
                                   /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}_${JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${FULL_JOB_NAME}" &
                                else
                                    if [[ ${JOB_NAME} == *"CpuStatsJob"* ]] || [[ ${JOB_NAME} == *"DiameterStatsJob"* ]] || [[ ${JOB_NAME} == *"DiskStatsJob"* ]]; then
                                       UTC_OFFSET='+0000'
                                       /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}${UTC_OFFSET}" "${ROP_END_TIME_STATS}${UTC_OFFSET}" "${LOG}_${JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${FULL_JOB_NAME}" &
                                    else
                                       /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}_${JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${FULL_JOB_NAME}" &
                                    fi
                                fi 
                            elif [[ ${NE} == *"VCUDB"* ]] ; then
                                if [[ $ROP_PERIOD_MIN == 15 ]] ; then
                                    VCUDB_JOB_CONFIGURATION=`echo $FULL_JOB_NAME | awk -F"|" '{print $1}'| awk -F":" '{print $2}'`
                                elif  [[ $ROP_PERIOD_MIN == 1 ]] ; then
                                    VCUDB_JOB_CONFIGURATION=`echo $FULL_JOB_NAME | awk -F"|" '{print $2}' | awk -F":" '{print $2}'`
                                fi
                                for VCUDB_JOB_NAME in $(echo $VCUDB_JOB_CONFIGURATION | sed "s/,/ /g"); do
                                    /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}_${VCUDB_JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${VCUDB_JOB_NAME}" ""
                                done 
                            else
                                /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}/${JOB_NAME}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}_${JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${FULL_JOB_NAME}" "${TSP_MPID_TIME_START_DATETIME}" &
                            fi
                        done

                    elif [[ ${NE} == *"FrontHaul"* ]] && [[ ${!stats_update_TZ} == "YES" ]]; then
                        /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${FILE_beginTime}" "${FILE_endTime}" "${dur}" &

                    elif [[ ${NE} == SCEF ]];then
                        file_types=${NE}_STATS_FILE_TYPES
                        for _file_type in ${!file_types};do
                            stats_file_format="${NE}"_STATS_TYPE_"${_file_type}"_OUTPUT_FILE_FORMAT
                            stats_output_type="${NE}"_STATS_TYPE_"${_file_type}"_OUTPUT_TYPE
                            stats_input_path=${stats_input_location}/${_file_type}
                            stats_TZ="$NE"_STATS_TYPE_"${_file_type}"_OUTPUT_TZ
                            stats_update_TZ="${NE}"_STATS_TYPE_"${_file_type}"_UPDATE_TZ
                            append_path="$NE"_STATS_TYPE_"${_file_type}"_APPEND_PATH

                            /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_path}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${_file_type}"
                        done
                    elif [[ ${NE} == "vAFG" ]] ; then
                        /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}_${JOB_NAME}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "" ""

                    #ORU stats files for GNODEBRADIONODE
                    elif [[ ${NE} == "gNodeBRadio" ]] ;then
                        if [[ ${ROP_PERIOD_MIN} == 15 ]];then
                            oru_info=${NE}_STATS_ORU_INFO
                            output_path=${!append_path}
                            for info in ${!oru_info};do
                               append_path=${output_path}/$(echo ${info} | awk -F"|" '{print $1}')
                               hardware_name=$(echo ${info} | awk -F"|" '{print $2}')
                               time_zone=$(echo ${info} | awk -F"|" '{print $3}')

                                if [[ ! -z ${time_zone} ]];then
                                    createTimeStampWithConfigTZ ${time_zone}
                                    DATE_REF=${DATE_REF_TZ}
                                    ROP_START_TIME_STATS=${ROP_START_TIME_TZ}${ROP_TZ_OFFSET}
                                    ROP_END_TIME_STATS=${ROP_END_TIME_TZ}${ROP_TZ_OFFSET}
                                    ROP_END_DATE=${ROP_END_DATE_TZ}
                                else
                                    DATE_REF=${DATE_LOCAL}
                                    ROP_START_TIME_STATS=${ROP_START_TIME_LOCAL}${ROP_LOCAL_OFFSET}
                                    ROP_END_TIME_STATS=${FH_ORAN_ROP_END_TIME_LOCAL}${FH_ORAN_ROP_LOCAL_END_OFFSET}
                                    ROP_END_DATE=${ROP_END_DATE_LOCAL}
                                fi
                                /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${append_path}" "${SIM_NAME}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "${hardware_name}"
                            done
                        fi
                    elif [[ ${NE} == *WMG*OI* ]] || [[ ${NE} == *ECEE* ]] || [[ ${NE} == *EPG*OI* ]] || [[ ${NE} == *vCU*UP* ]] || [[ ${NE} == *vCU*CP* ]] || [[ ${NE} == *ADP* ]];then
                        /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${old_NE}" "${!stats_file_format}" "${!stats_output_type}" "${stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "" "" "${epoch_rop_folder}" ${LOCK_FILE} &
                    else
                        /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${NE}" "${!stats_file_format}" "${!stats_output_type}" "${!stats_input_location}" "${DATE_REF}" "${ROP_START_TIME_STATS}" "${ROP_END_TIME_STATS}" "${LOG}" "stats" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" "" "" "${epoch_rop_folder}" ${LOCK_FILE} &
                    fi
                fi

                #For EVENTS file generation
                events="$NE"_GENRATE_EVENTS
                if [[ ${!events} == "YES" ]] ; then
                    events_file_format="${NE}"_EVENTS_OUTPUT_FILE_FORMAT
                    events_output_type="${NE}"_EVENTS_OUTPUT_TYPE
                    events_input_location="${NE}"_EVENTS_INPUT_LOCATION
                    script="startEventsPlayback.sh"
                    events_TZ="$NE"_EVENTS_OUTPUT_TZ
                    append_path="$NE"_PMEvent_FileLocation
                    if [[ -z ${!append_path} ]];then
                        append_path="$NE"_EVENTS_APPEND_PATH
                    fi
                    if [[ ${!events_TZ} == "LOCAL" ]] ; then
                        DATE_REF=${DATE_LOCAL}
                        ROP_START_TIME_EVENTS=${ROP_START_TIME_LOCAL}${ROP_LOCAL_OFFSET}
                        ROP_END_TIME_EVENTS=${ROP_END_TIME_LOCAL}${ROP_LOCAL_END_OFFSET}
                        ROP_END_DATE=${ROP_END_DATE_LOCAL}
                    else
                        DATE_REF=${DATE}
                        ROP_START_TIME_EVENTS=${ROP_START_TIME}
                        ROP_END_TIME_EVENTS=${ROP_END_TIME}
                        ROP_END_DATE=${ROP_END_DATE_UTC}
                    fi
                    /${INSTALL_DIR}/startFileDistribution.sh "${PM_DIR}" "${!append_path}" "${SIM_NAME}" "${!events_file_format}" "${!events_output_type}" "${!events_input_location}" "${DATE_REF}" "${ROP_START_TIME_EVENTS}" "${ROP_END_TIME_EVENTS}" "${LOG}" "events" "${script}" "${ROP_PERIOD_MIN}" "${ROP_END_DATE}" &
                fi
             break
            fi
        done
    fi
done

wait
touch "/netsim_users/pms/config/touch_files/${epoch_rop_folder/_/|},PLAYBACK"
log "End ${STARTDATE_UTC}"


