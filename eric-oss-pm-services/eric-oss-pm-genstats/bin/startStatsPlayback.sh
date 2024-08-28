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
# Version no    :  NSS 22.12
# Purpose       :  The purpose of this script to call playbackGenerator framework to generate STATS PM files.
# Jira No       :  NSS-39552
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/12495832/
# Description   :  Adding 12mb file support for vCU-CP and vCU-UP in MD_1
# Date          :  16/05/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

#Fetching input arguments
PM_DIR=${1}
APPEND_PATH=${2}
NE_TYPE=${3}
FILE_FORMAT=${4}
OUTPUT_TYPE=${5}
INPUT_LOCATION=${6}
DATE=${7}
ROP_START_TIME=${8}
ROP_END_TIME=${9}
INSTALL_DIR=${10}
LOG=${11}
FINAL_MAPPED_FILE=${12}
PROCESS_TYPE=${13}
ROP_PERIOD=${14}
ROP_END_DATE=${15}
dur=${18}
epoch_rop_folder=${19}
LOCK_FILE=${20}

UNIQUE_ID="99999"
CREATE_MOUNT_SCRIPT="/netsim_users/pms/bin/createTempFsMountForNodes.sh"

if [[ $NE_TYPE == *"SBG-IS"* ]]; then
    UNIQUE_ID=${16}
elif [[ $NE_TYPE == *"HSS-FE-TSP"* ]] || [[ $NE_TYPE == *"MTAS-TSP"* ]] || [[ $NE_TYPE == *"CSCF-TSP"* ]] || [[ $NE_TYPE == *"SAPC-TSP"* ]] || [[ $NE_TYPE == *"vEIR-FE"* ]] || [[ $NE_TYPE == *"EIR-FE"* ]]  || [[ $NE_TYPE == *"VCUDB"* ]]; then
    MEASUREMENT_JOB_ID_MPID=${16}
    MEASUREMENT_JOB_ID=`echo $MEASUREMENT_JOB_ID_MPID | cut -d":" -f1`
    MP_COUNT=`echo $MEASUREMENT_JOB_ID_MPID | cut -d":" -f2`
    if [[ ! $NE_TYPE == *"EIR-FE"* ]]; then
       MP_START=`echo $MEASUREMENT_JOB_ID_MPID | cut -d":" -f3`
       TSP_MPID_TIME_START_DATETIME=${17}
    fi
elif [[ $NE_TYPE == *"FrontHaul"* ]] && [[ $dur == "900" ]] || [[ $dur == "60" ]] || [[ $dur == "86400" ]]; then
    FILE_beginTime=${16}
    FILE_endTime=${17}
    dur=${18}
elif [[ $NE_TYPE == *"SCEF"* ]]; then
    FILE_TYPE=${16}
elif [[ $NE_TYPE == *"gNodeBRadio"* ]]; then
    HARDWARE_NAME=${16}
fi

NRM_CHECK=1
MD_1_CHECK=1

DEPL_TYPE=$(cat /netsim/netsim_cfg | grep -v '#' | grep 'TYPE=' | awk -F'"' '{print $2}')

if [[ ${DEPL_TYPE} == *"NRM"* ]] ; then
    NRM_CHECK=0
elif [[ ${DEPL_TYPE} == "MD_1" ]] ; then
    MD_1_CHECK=0
fi

LOOP_INSTANCE=1

#logging
log() {

    MSG=$1

    TS=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${TS} ${MSG}"
}

#Create mounting for node path in pms_tmpfs and netsim_dbdir 
mountOutputDir() {

    OUTDIR=$1
    NODEDIR=$2

    mkdir -p ${OUTDIR}
    if [[ -d ${OUTDIR} ]];then 
        echo "INFO: createTempFsMountForNodes.sh"
        echo shroot | su root -c "${CREATE_MOUNT_SCRIPT} ${OUTDIR} ${NODEDIR}"
        if [ $? -ne 0 ] ; then
            echo "ERROR: createTempFsMountForNodes.sh failed"
            exit 1
        fi
    fi
}

generatePmFile(){

    NEW_FILE_NAME=$(echo ${FILE_FORMAT} | sed "s/<DATE>/${DATE}/; s/<ROP_START_TIME>/${ROP_START_TIME}/; s/<ROP_END_TIME>/$ROP_END_TIME/; s/<ROP_END_DATE>/${ROP_END_DATE}/; s/<MEASUREMENT_JOB_NAME>/${MEASUREMENT_JOB_ID}/; s/<MANAGED_ELEMENT_ID>/${targetDir}/; s/<DOMAIN>/${sourceFileName}/; s/<HARDWARE_NAME>/${HARDWARE_NAME}/")

    #for(( inst=1; inst <= ${LOOP_INSTANCE}; inst++ )); do
        FILE_NAME=$(echo ${NEW_FILE_NAME} | sed "s/UNIQUE_ID/$UNIQUE_ID/")
        outputFile=${OUTPUT_PATH}/${NEW_FILE_NAME}

            if [ ! -f $outputFile ]; then
                ln -sf $sourceFile $outputFile
            fi
            rc=$?
            if [ $rc -ne 0 ] ; then
                if [ $rc -eq 2 ] ; then
                    log "INFO: File exists: $target"
                else
                    log "ERROR: Failed to link $target"
                fi
            fi
}

for fname in `cat ${FINAL_MAPPED_FILE}`; do
    sourceFile=${INPUT_LOCATION}/$(echo $fname | cut -d";" -f1)
    targetDir=`echo $fname | cut -d";" -f2`
    startedDir=`echo $targetDir | awk -F'=' '{print $4}'`
    if ! grep -q ${startedDir} "/tmp/showstartednodes.txt"; then
        continue
    fi
    OUTPUT_PATH=${PM_DIR}/${targetDir}/${epoch_rop_folder}/
    if [[ ! -f $OUTPUT_PATH ]]; then
        mkdir -p ${OUTPUT_PATH}
    fi
    generatePmFile
done


rm -rf ${LOCK_FILE}
