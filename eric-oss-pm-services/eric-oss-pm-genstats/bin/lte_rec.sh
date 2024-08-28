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
# Version no    :  NSS 21.07
# Purpose       :  Script is responsible for generating links for Events
# Jira No       :  NSS-34236
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/10281485/
# Description   :  Adding support for  SGSN MME in MD_1
# Date          :  29/07/2021
# Last Modified :  manali.singh@tcs.com
####################################################

. /netsim/netsim_cfg > /dev/null 2>&1

umask 000

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

REC_TEMPLATE_DIR=/netsim_users/pms/rec_templates
MME_REF_CFG=/netsim_users/pms/etc/sgsn_mme_ebs_ref_fileset.cfg

OUT_ROOT=/netsim_users
if [ -d /pms_tmpfs ] ; then
    OUT_ROOT=/pms_tmpfs
fi

OUT_ROOT=/ericsson/pmic/CELLTRACE/
DG2_COUNTER=0

TMPFS_REC_TEMPLATES_DIR="/pms_tmpfs/xml_step/recording_templates"
if [[ ! -d ${TMPFS_REC_TEMPLATES_DIR} ]] ; then
   mkdir -p ${TMPFS_REC_TEMPLATES_DIR}
fi


# Check if LTE UETRACE MCC MNC set in netsim_cfg
DEFAULT_MCC_MNC="3530570"
if [ -z "${MCC_MNC}" ] ; then
    MCC_MNC=$DEFAULT_MCC_MNC
fi

# Check if 3GPP MCC MNC set in netsim_cfg
DEFAULT_MCC_MNC_3GPP="5303750"
if [ -z "${MCC_MNC_3GPP}" ] ; then
    MCC_MNC_3GPP=$DEFAULT_MCC_MNC_3GPP
fi
SIM_TYPE_FILE="/netsim/genstats/tmp/sim_info.txt"

SPECIFIC_CELLTRACE="LTE"
nr_count=0

if [[ ${TYPE} != "NSS" ]]; then
    if [[ ${TYPE} == "NRM1.2" ]] || [[ ${TYPE} == "NRM3" ]] || [[ ${TYPE} == "NRM4" ]] || [[ ${TYPE} == "NRM4.1" ]] || [[ ${TYPE} == "NRM5" ]] || [[ ${TYPE} == "NRM5.1" ]]; then
        if [[ ! -z ${LTE_CELLTRACE_19MB_NODE} ]] ; then
            available_count=$(find /netsim/netsim_dbdir/simdir/netsim/netsimdir/ -type d -name "${LTE_CELLTRACE_19MB_NODE}" | grep -w "${LTE_CELLTRACE_19MB_NODE}" | wc -l )
            if [[ ${available_count} -eq 1 ]]; then
                if [[ -f ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ]] ; then
                    SPECIFIC_CELLTRACE="LTE"
                else
                    log "ERROR: File ${LTE_CELLTRACE_19MB_FILE} not found in ${REC_TEMPLATE_DIR} dir."
                fi
            fi
        fi
    else
        if [[ ! -z ${LTE_CELLTRACE_30MB_NODE} ]] ; then
            available_count=$(find /netsim/netsim_dbdir/simdir/netsim/netsimdir/ -type d -name "${LTE_CELLTRACE_30MB_NODE}" | grep -w "${LTE_CELLTRACE_30MB_NODE}" | wc -l )
            if [[ ${available_count} -eq 1 ]]; then
                if [[ -f ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_30MB_FILE} ]] ; then
                    SPECIFIC_CELLTRACE="LTE_30MB"
                else
                    log "ERROR: File ${LTE_CELLTRACE_30MB_FILE} not found in ${REC_TEMPLATE_DIR} dir."
                fi
            fi
        fi
        if [[ ! -z ${NRAT_CELLTRACE_30MB_NODE} ]]; then
            associated_sim=$(find /netsim/netsim_dbdir/simdir/netsim/netsimdir/ -type d -name "${NRAT_CELLTRACE_30MB_NODE}" | grep -w "${NRAT_CELLTRACE_30MB_NODE}" | rev | awk -F'/' '{print $2}' | rev )
            if [[ ! -z ${associated_sim} ]]; then
                sim_property=$(cat ${SIM_TYPE_FILE} | grep "${associated_sim}:" | awk -F':' '{print $3}')
                if [[ ${sim_property} == "MixedNRAT" ]]; then
                    if [[ ! -f ${REC_TEMPLATE_DIR}/${NRAT_CELLTRACE_30MB_FILE} ]] ; then
                        log "ERROR: File ${NRAT_CELLTRACE_30MB_FILE} not found in ${REC_TEMPLATE_DIR} dir."
                    fi
                    SPECIFIC_CELLTRACE="NRAT_30MB"
                fi
            fi
        fi
    fi
fi

FILE_TYPES="CELLTRACE"
while getopts  "r:f:x:j:" flag
do
    case "$flag" in
        r) ROP_PERIOD_MIN="$OPTARG";;
        f) FILE_TYPES="$OPTARG";;
        x) EXEC_FROM_HC="$OPTARG";;
        j) CURRENT_EPOCH="$OPTARG";;
        *) printf "Usage: %s [-r rop interval in mins] [-f file types EBS:EBM:CELLTRACE:UETRACE:CTUM] \n" $0
           exit 1;;
    esac
done

if [ -z ${ROP_PERIOD_MIN} ] ; then
    ROP_PERIOD_MIN=15
fi

# This file is used to persist the EBS file index value for MME EBS files
if [ ! -f "${REC_TEMPLATE_DIR}/.ebs_${ROP_PERIOD_MIN}" ] ; then
    echo "1" > "${REC_TEMPLATE_DIR}/.ebs_${ROP_PERIOD_MIN}"
fi

# This file is used to persist the rop index value for MME UETRACE files
if [ ! -f "${REC_TEMPLATE_DIR}/.uetrace" ] ; then
    echo "0" > "${REC_TEMPLATE_DIR}/.uetrace"
fi


# This file is used to persist the rop index value for MME UETRACE files
if [ ! -f "${REC_TEMPLATE_DIR}/.ctum" ] ; then
    echo "0" > "${REC_TEMPLATE_DIR}/.ctum"
fi

############################# SET ROP TIMINIGS #############################
# Generate Epoch Seconds (UTC always)
current_epoch=$(date +%s)

if [[ ! -z $CURRENT_EPOCH ]]; then
    current_epoch=$CURRENT_EPOCH
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

DATE=$(date -u -d @${start_epoch} +'%Y%m%d')
ROP_START_TIME=$(date -u -d @${start_epoch} +'%H%M')
ROP_END_TIME=$(date -u -d @${end_epoch} +'%H%M')
epoch_rop="${start_epoch}_${end_epoch}"
MME_TZ=`date +'%Z'`
if [ ! -z "${SGSN_TZ}" ] ; then
    MME_TZ="${SGSN_TZ}"
fi

#FOR MME Nodes
ROP_START_DATE_LOCAL=$(TZ=${MME_TZ} date -d @${start_epoch} +'%Y%m%d')
ROP_START_TIME_LOCAL=$(TZ=${MME_TZ} date -d @${start_epoch} +'%H%M')
ROP_START_OFFSET=$(TZ=${MME_TZ} date -d @${start_epoch} +'%z')

ROP_END_DATE_LOCAL=$(TZ=${MME_TZ} date -d @${end_epoch} +'%Y%m%d')
ROP_END_TIME_LOCAL=$(TZ=${MME_TZ} date -d @${end_epoch} +'%H%M')
ROP_END_OFFSET=$(TZ=${MME_TZ} date -d @${end_epoch} +'%z')

if [[ ${ROP_START_OFFSET} != ${ROP_END_OFFSET} ]];then
     MME_UTC_START_TIME=$(date -u -d @${start_epoch} +'%H%M')
     MME_OFFSET_TYPE=$(echo ${ROP_END_OFFSET} | cut -c 1)
     MME_OFFSET_HOUR=$(echo ${ROP_END_OFFSET} | cut -c 2,3)
     MME_OFFSET_MIN=$(echo ${ROP_END_OFFSET} | cut -c 4,5)
     if [[ ${MME_OFFSET_TYPE} == "+" ]];then
        ROP_START_TIME_LOCAL=$(date -u -d "${MME_UTC_START_TIME} +${MME_OFFSET_HOUR} hour $MME_OFFSET_MIN minutes " +"%H%M")
     else
        ROP_START_TIME_LOCAL=$(date -u -d "${MME_UTC_START_TIME} -${MME_OFFSET_HOUR} hour $MME_OFFSET_MIN minutes " +"%H%M")
     fi
     ROP_START_OFFSET=${ROP_END_OFFSET}
fi

############################################################################

EBS_FILENAME_PREFIX="A${ROP_START_DATE_LOCAL}.${ROP_START_TIME_LOCAL}${ROP_START_OFFSET}-${ROP_END_DATE_LOCAL}.${ROP_END_TIME_LOCAL}${ROP_END_OFFSET}_"

MME_CTUM_FILENAME_PREFIX="A${ROP_START_DATE_LOCAL}.${ROP_START_TIME_LOCAL}${ROP_START_OFFSET}-${ROP_END_DATE_LOCAL}.${ROP_END_TIME_LOCAL}${ROP_END_OFFSET}_"

MME_UETRACE_FILENAME_PREFIX="B${ROP_START_DATE_LOCAL}.${ROP_START_TIME_LOCAL}${ROP_START_OFFSET}-${ROP_END_DATE_LOCAL}.${ROP_END_TIME_LOCAL}${ROP_END_OFFSET}"

processSim() {
    MY_SIM=$1
    echo "${FILE_TYPES}" | egrep -w "ALL|CELLTRACE" > /dev/null
    if [ $? -eq 0 ] ; then
        #echo "Generating CELLTRACE files"
        generateCELLTRACE ${MY_SIM}
    fi

    echo "${FILE_TYPES}" | egrep -w "ALL|UETRACE" > /dev/null
    if [ $? -eq 0 ] ; then
        #echo "Generating ERBS UETRACE files"
        generateERBSUETRACE ${MY_SIM}
    fi

}



#Create mounting for node path in pms_tmpfs and netsim_dbdir
createOutputDir() {

    OUTDIR=$1
    NODEDIR=$2
    CREATE_MOUNT_SCRIPT="/netsim_users/pms/bin/createTempFsMountForNodes.sh"

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

generateCELLTRACE() {

    MY_SIM=$1

    #Ignore MSRBS_V1(pERBS) and  MSRBS_V2(dg2ERBS)
    ERBS_NODE_LIST=`ls ${OUT_ROOT} | grep RBS | grep -v pERBS | grep -v dg2ERBS | grep -v MSRBS-V2 | grep -v PC | grep -v gNodeB | grep -v LTE`
    VTF_NODE_LIST=`ls ${OUT_ROOT} | grep -i VTFRADIONODE`

    MSRBS_V1_NODE_LIST=`ls ${OUT_ROOT} | grep pERBS`
    MSRBS_V2_NODE_LIST=""
    if [[ "${SIM_BEHAVIOUR}" == "MixedNRAT" ]]; then
        MSRBS_V2_NODE_LIST=`ls ${OUT_ROOT} | egrep -i 'dg2ERBS|MSRBS-V2|gNodeBRadio'`
    else
        MSRBS_V2_NODE_LIST=`cat /tmp/showstartednodes.txt | egrep -i 'dg2ERBS|MSRBS-V2' | grep $MY_SIM | grep "<CTR>" | awk -F" " '{print $1}'`
    fi

    # Make sure we have the CellTraceFilesLocation
    for NODE in ${ERBS_NODE_LIST} ; do
        NODE_PM_DATA=${OUT_ROOT}/${NODE}/
        FILE="CellTraceFilesLocation"
        if [ ! -r ${NODE_PM_DATA}/${FILE} ] ; then
            log "WARN: ${NODE_PM_DATA}/${FILE} is missing, creating"
            echo "/" > ${NODE_PM_DATA}/${FILE}
        fi
    done

    if [ ! -z "${ERBS_NODE_LIST}" ] ; then

        if [ -z "${LTE_CELLTRACE_LIST}" ] ; then
            log "ERROR: LTE_CELLTRACE_LIST not set"
            exit 1
        fi
        #
        # CellTrace for ERBS
        #
        for LTE_CELLTRACE in ${LTE_CELLTRACE_LIST} ; do
            #<Type><Date>.<StartTime>-<EndTime>_CellTrace_DU<No>_<RC>.bin.gz
            IN_FILE_NAME=`echo ${LTE_CELLTRACE} | awk -F: '{print $1}'`
            DU_NUM=`echo ${LTE_CELLTRACE} | awk -F: '{print $2}'`
            REC_TYPE=`echo ${LTE_CELLTRACE} | awk -F: '{print $3}'`

            IN_FILE_PATH="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
            OUT_FILE_NAME="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_CellTrace_DUL${DU_NUM}_${REC_TYPE}.bin.gz"
            TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${IN_FILE_NAME}"

            if [ ! -r ${IN_FILE_PATH} ] ; then
                log "ERROR: Cannot find ${IN_FILE_PATH}"
                exit 1
            else
                if [ ! -r ${TMPFS_IN_FILE} ] ; then
                  copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                fi
            fi

            for NODE in ${ERBS_NODE_LIST} ; do
                if grep -q ${node} "/tmp/showstartednodes.txt" | grep STATS; then
                    NODE_PM_DATA=${OUT_ROOT}/${NODE}/
                    if [[ ${SPECIFIC_CELLTRACE} == "LTE" ]]; then
                        if [[ ${NODE} == ${LTE_CELLTRACE_19MB_NODE} && ${REC_TYPE} = 1 ]]; then
                            #ln -s ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                            if [ ! -r ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ] ; then
                                log "ERROR: Cannot find ${LTE_CELLTRACE_19MB_FILE}"
                                exit 1
                            else
                                if [ ! -r ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_19MB_FILE} ] ; then
                                    copySourceTemplates ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ${TMPFS_REC_TEMPLATES_DIR}
                                fi
                            fi

                            cp ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_19MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                        else
                            cp ${TMPFS_IN_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                        fi
                    elif [[ ${SPECIFIC_CELLTRACE} == "LTE_30MB" ]]; then
                        if [[ ${NODE} == ${LTE_CELLTRACE_30MB_NODE} && ${REC_TYPE} = 1 ]]; then
                            if [ ! -r ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_30MB_FILE} ] ; then
                                log "ERROR: Cannot find ${LTE_CELLTRACE_30MB_FILE}"
                                exit 1
                            else
                                if [ ! -r ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_30MB_FILE} ] ; then
                                    copySourceTemplates ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_30MB_FILE} ${TMPFS_REC_TEMPLATES_DIR}
                                fi
                            fi
                            ln -s ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_30MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                        else
                            ln -s ${TMPFS_IN_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME} >> /dev/null
                        fi
                    else
                        ln -s ${TMPFS_IN_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    fi
                fi
            done
        done
    fi



    #For MSRBS_V1 nodes
    if [ ! -z "${MSRBS_V1_NODE_LIST}" ] ; then

        if [ -z "${MSRBS_V1_LTE_CELLTRACE_LIST}" ] ; then
            log "ERROR: MSRBS_V1_LTE_CELLTRACE_LIST not set"
            exit 1
        fi

        FILE_PATH="//"
        if [ ! -z "${MSRBS_V1_PMEvent_FileLocation}" ] ; then
            FILE_PATH=${MSRBS_V1_PMEvent_FileLocation}
        fi
        #
        # CellTrace for MSRBS_V1
        #
        for LTE_CELLTRACE in ${MSRBS_V1_LTE_CELLTRACE_LIST} ; do
            #<Type><Date>.<StartTime>-<EndTime>_CellTrace_DU<No>_<RC>.bin.gz
            IN_FILE_NAME=`echo ${LTE_CELLTRACE} | awk -F: '{print $1}'`
            JOB_NUM=`echo ${LTE_CELLTRACE} | awk -F: '{print $2}'`
            REC_TYPE=`echo ${LTE_CELLTRACE} | awk -F: '{print $3}'`

            IN_FILE_PATH="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
            TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${IN_FILE_NAME}"

            if [ ! -r ${IN_FILE_PATH} ] ; then
                log "ERROR: Cannot find ${IN_FILE_PATH}"
                exit 1
            else
                if [ ! -r ${TMPFS_IN_FILE} ] ; then
                  copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                fi
            fi


            for NODE in ${MSRBS_V1_NODE_LIST} ; do
                NODE_PM_DATA=${OUT_ROOT}/${NODE}/${FILE_PATH}
                OUT_FILE_NAME="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_${NODE}.Lrat_${JOB_NUM}_${REC_TYPE}.bin.gz"
                ln -s ${TMPFS_IN_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
            done
        done
    fi

    #For MSRBS_V2 nodes
    if [[ ! -z "${MSRBS_V2_NODE_LIST}" ]] ; then

        if [ -z "${MSRBS_V2_LTE_CELLTRACE_LIST}" ] ; then
            log "ERROR: MSRBS_V2_LTE_CELLTRACE_LIST not set"
            exit 1
        fi

        FILE_PATH="//"
        if [ ! -z "${MSRBS_V2_PMEvent_FileLocation}" ] ; then
            FILE_PATH=${MSRBS_V2_PMEvent_FileLocation}
        fi

        #
        # CellTrace for MSRBS_V2
        #

        SIM_BEHAVIOUR=$(cat ${SIM_TYPE_FILE} | grep "${SIM}:" | rev | awk -F':' '{print $1}' | rev )

        if [[ ! -z ${SIM_BEHAVIOUR} ]] && [[ ${SIM_BEHAVIOUR} == "DualBB" ]]; then
            MSRBS_V2_LTE_CELLTRACE_LIST="celltrace_768K.bin.gz:1:1 celltrace_768K.bin.gz:1:3 celltrace_768K.bin.gz:3:1 celltrace_768K.bin.gz:3:3"
        fi

        for LTE_CELLTRACE in ${MSRBS_V2_LTE_CELLTRACE_LIST} ; do
            #<Type><Date>.<StartTime>-<EndTime>_CellTrace_DU<No>_<RC>.bin.gz
            IN_FILE_NAME=`echo ${LTE_CELLTRACE} | awk -F: '{print $1}'`
            DU_NUM=`echo ${LTE_CELLTRACE} | awk -F: '{print $2}'`
            REC_TYPE=`echo ${LTE_CELLTRACE} | awk -F: '{print $3}'`

            IN_FILE_PATH="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
            TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${IN_FILE_NAME}"


            if [ ! -r ${IN_FILE_PATH} ] ; then
                log "ERROR: Cannot find ${IN_FILE_PATH}"
                exit 1
            else
                if [ ! -r ${TMPFS_IN_FILE} ] ; then
                  copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                fi
            fi

            for NODE in ${MSRBS_V2_NODE_LIST} ; do
                NODE="SubNetwork=Europe,SubNetwork=Ireland,MeContext=${NODE}"
                if [[ ! -d ${OUT_ROOT}/${NODE} ]]; then
                    continue
                fi
                OUT_FILE_NAME="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_CellTrace_SubNetwork=Europe,SubNetwork=Ireland,MeContext=${NODE}_DUL${DU_NUM}_${REC_TYPE}.bin.gz"
                NODE_PM_DATA=${OUT_ROOT}/${NODE}/${FILE_PATH}/${epoch_rop}/
                if [[ ! -d ${NODE_PM_DATA} ]]; then
                    mkdir -p ${NODE_PM_DATA}
                fi
                if [[ ${SPECIFIC_CELLTRACE} == "LTE" ]]; then
                    if [[ ${NODE} == ${LTE_CELLTRACE_19MB_NODE} && ${REC_TYPE} = 1 ]]; then
                       if [ ! -r ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ] ; then
                          log "ERROR: Cannot find ${LTE_CELLTRACE_19MB_FILE}"
                          exit 1
                        else
                          if [ ! -r ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_19MB_FILE} ] ; then
                              copySourceTemplates ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_19MB_FILE} ${TMPFS_REC_TEMPLATES_DIR}
                          fi
                        fi

                        cp ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_19MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    else
                        if [[ ! -f ${NODE_PM_DATA}/${OUT_FILE_NAME} ]]; then
                            ln -s ${TMPFS_IN_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                        fi
                    fi
                elif [[ ${SPECIFIC_CELLTRACE} == "LTE_30MB" ]]; then
                    if [[ ${NODE} == ${LTE_CELLTRACE_30MB_NODE} && ${REC_TYPE} = 1 ]]; then
                       if [ ! -r ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_30MB_FILE} ] ; then
                          log "ERROR: Cannot find ${LTE_CELLTRACE_30MB_FILE}"
                          exit 1
                        else
                          if [ ! -r ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_30MB_FILE} ] ; then
                           copySourceTemplates ${REC_TEMPLATE_DIR}/${LTE_CELLTRACE_30MB_FILE} ${TMPFS_REC_TEMPLATES_DIR}
                          fi
                        fi

                        ln -s ${TMPFS_REC_TEMPLATES_DIR}/${LTE_CELLTRACE_30MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    else
                        ln -s ${TMPFS_IN_FILE}   ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    fi
                elif [[ ${SPECIFIC_CELLTRACE} == "NRAT_30MB" ]]; then
                    if [[ ${NODE} == ${NRAT_CELLTRACE_30MB_NODE} && ${REC_TYPE} = 1 ]]; then
                       if [ ! -r ${REC_TEMPLATE_DIR}/${NRAT_CELLTRACE_30MB_FILE} ] ; then
                          log "ERROR: Cannot find ${NRAT_CELLTRACE_30MB_FILE}"
                          exit 1
                        else
                        if [ ! -r ${TMPFS_REC_TEMPLATES_DIR}/${NRAT_CELLTRACE_30MB_FILE} ] ; then
                           copySourceTemplates ${REC_TEMPLATE_DIR}/${NRAT_CELLTRACE_30MB_FILE} ${NRAT_CELLTRACE_30MB_FILE}
                           fi
                        fi

                        ln -s ${TMPFS_REC_TEMPLATES_DIR}/${NRAT_CELLTRACE_30MB_FILE} ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    else
                        ln -s ${TMPFS_IN_FILE}  ${NODE_PM_DATA}/${OUT_FILE_NAME}
                    fi
                fi
            done

        done
    fi

    if [ ! -z "${VTF_NODE_LIST}" ] ; then

        if [ -z "${VTF_CELLTRACE_LIST}" ] ; then
            log "ERROR: VTF_CELLTRACE_LIST not set"
            exit 1
        fi
        #
        # CellTrace for VTF
        #

        VTF_FILE_PATH="//"
        if [ ! -z "${VTFRADIONODE_PMEvent_FileLocation}" ] ; then
            VTF_FILE_PATH=${VTFRADIONODE_PMEvent_FileLocation}
        fi

        for VTF_CELLTRACE in ${VTF_CELLTRACE_LIST} ; do
            #<Type><Date>.<StartTime>-<EndTime>_CellTrace_DU<No>_<RC>.bin.gz
            IN_FILE_NAME=`echo ${VTF_CELLTRACE} | awk -F: '{print $1}'`
            DU_NUM=`echo ${VTF_CELLTRACE} | awk -F: '{print $2}'`
            REC_TYPE=`echo ${VTF_CELLTRACE} | awk -F: '{print $3}'`

            IN_FILE_PATH="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
            OUT_FILE_NAME="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_CellTrace_DUL${DU_NUM}_${REC_TYPE}.bin.gz"

            if [ ! -r ${IN_FILE_PATH} ] ; then
                log "ERROR: Cannot find ${IN_FILE_PATH}"
                exit 1
            fi

            for NODE in ${VTF_NODE_LIST} ; do
                NODE_PM_DATA=${OUT_ROOT}/${NODE}/${VTF_FILE_PATH}
                if [ ! -d "${NODE_PM_DATA}" ] ; then
                    mkdir -p ${NODE_PM_DATA}
                fi
                ln -s ${IN_FILE_PATH} ${NODE_PM_DATA}/${OUT_FILE_NAME}
            done
        done
    fi

}


generateERBSUETRACE() {
    MY_SIM=$1

    #Ignore MSRBS_V1(pERBS) and  MSRBS_V2(dg2ERBS)
    ERBS_NODE_LIST=($(ls ${OUT_ROOT}/ | grep RBS | grep -v pERBS | grep -v dg2ERBS))

    pERBS_NODE_LIST=($(ls ${OUT_ROOT}/ | grep pERBS))

    MSRBS_V2_NODE_LIST=($(ls ${OUT_ROOT}/ | egrep 'dg2ERBS|ERBS'))

    declare -a NRAT_NODE_LIST
    if [[ ${TYPE} == "NRM6.3" ]]; then
        NRAT_NODE_LIST=($(ls ${OUT_ROOT}/ | grep 'gNodeBRadio'))
    fi

    declare -a VTF_NODE_LIST
    if [[ "${ROP_PERIOD_MIN}" = "15" ]]; then
       VTF_NODE_LIST=($(ls ${OUT_ROOT} | grep -i VTFRADIONODE))
    fi

    VTF_NODE_COUNT=0

    if [ ! -z ${VTF_NODE_LIST} ]; then
        VTF_NODE_COUNT=`ls ${OUT_ROOT} | grep -i VTFRADIONODE | wc -l`
    fi

    # Make sure we have the UeTraceFilesLocation
    for NODE in ${ERBS_NODE_LIST[@]} ; do
        NODE_PM_DATA=${OUT_ROOT}/${NODE}/
        FILE="UeTraceFilesLocation"
        if [ ! -r ${NODE_PM_DATA}/${FILE} ] ; then
            log "WARN: ${NODE_PM_DATA}/${FILE} is missing, creating"
            echo "/" > ${NODE_PM_DATA}/${FILE}
        fi

    done

    if [ ! -z "${ERBS_NODE_LIST}" ] ; then
        # removed as per https://jira-nam.lmera.ericsson.se/browse/NSS-6488
        #if [ -z "${LTE_UETRACE_LIST}" ] ; then
        #    log "ERROR: LTE_UETRACE_LIST not set"
        #    exit 1
        #fi
        #
        # UETrace
        #
        for LTE_UETRACE in ${LTE_UETRACE_LIST} ; do
            UETRACE_SIM=`echo ${LTE_UETRACE} | awk -F: '{print $2}'`
            if [ "${UETRACE_SIM}" = "${MY_SIM}" ] ; then
                UETRACE_FILE=`echo ${LTE_UETRACE} | awk -F: '{print $1}'`
                START_NE=`echo ${LTE_UETRACE} | awk -F: '{print $3}'`
                NUM_NE=`echo ${LTE_UETRACE} | awk -F: '{print $4}'`
                START_REF=`echo ${LTE_UETRACE} | awk -F: '{print $5}'`
                NUM_REF=`echo ${LTE_UETRACE} | awk -F: '{print $6}'`

                IN_FILE_PATH="${REC_TEMPLATE_DIR}/${UETRACE_FILE}"
                TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${UETRACE_FILE}"

                if [ ! -r ${IN_FILE_PATH} ] ; then
                   log "ERROR: Cannot find ${IN_FILE_PATH}"
                   exit 1
                else
                   if [ ! -r ${TMPFS_IN_FILE} ] ; then
                     copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                   fi
                fi


                if [ ${#ERBS_NODE_LIST[@]} -lt ${NUM_NE} ]; then
                    NUM_NE=${#ERBS_NODE_LIST[@]}
                fi

                CURR_REF=${START_REF}
                END_REF=`expr ${START_REF} + ${NUM_REF} - 1`

                CURR_NE=${START_NE}
                END_NE=`expr ${START_NE} + ${NUM_NE} - 1`

                while [ ${CURR_REF} -le ${END_REF} ] ; do

                    REF=`printf "%s1%04X" ${MCC_MNC} ${CURR_REF}`
                    NODE=`echo ${ERBS_NODE_LIST[${CURR_NE} - 1]}`

                    ln -s ${TMPFS_IN_FILE} ${OUT_ROOT}/${NODE}//A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF}.bin.gz

                    CURR_REF=`expr ${CURR_REF} + 1`
                    CURR_NE=`expr ${CURR_NE} + 1`
                    if [ ${CURR_NE} -gt ${END_NE} ] ; then
                        CURR_NE=${START_NE}
                    fi
                done
            fi
        done
    fi

    if [ ! -z "${MSRBS_V2_NODE_LIST}" ] ; then
        # removed as per https://jira-nam.lmera.ericsson.se/browse/NSS-6488
        #if [ -z "${MSRBS_V2_LTE_UETRACE_LIST}" ] ; then
        #    log "ERROR: MSRBS_V2_LTE_UETRACE_LIST not set"
        #    exit 1
        #fi
        FILE_PATH="//"
        if [ ! -z "${MSRBS_V2_PMEvent_FileLocation}" ] ; then
            FILE_PATH=${MSRBS_V2_PMEvent_FileLocation}
        fi

        #
        # UETrace
        #
        for LTE_UETRACE in ${MSRBS_V2_LTE_UETRACE_LIST} ; do
            UETRACE_SIM=`echo ${LTE_UETRACE} | awk -F: '{print $2}'`
            if [ "${UETRACE_SIM}" = "${MY_SIM}" ] ; then
                UETRACE_FILE=`echo ${LTE_UETRACE} | awk -F: '{print $1}'`
                START_NE=`echo ${LTE_UETRACE} | awk -F: '{print $3}'`
                NUM_NE=`echo ${LTE_UETRACE} | awk -F: '{print $4}'`
                START_REF=`echo ${LTE_UETRACE} | awk -F: '{print $5}'`
                NUM_REF=`echo ${LTE_UETRACE} | awk -F: '{print $6}'`

                IN_FILE_PATH="${REC_TEMPLATE_DIR}/${UETRACE_FILE}"
                TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${UETRACE_FILE}"

                if [ ! -r ${IN_FILE_PATH} ] ; then
                   log "ERROR: Cannot find ${IN_FILE_PATH}"
                   exit 1
                else
                   if [ ! -r ${TMPFS_IN_FILE} ] ; then
                     copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                   fi
                fi


                if [ ${#MSRBS_V2_NODE_LIST[@]} -lt ${NUM_NE} ]; then
                    NUM_NE=${#MSRBS_V2_NODE_LIST[@]}
                fi

                CURR_REF=${START_REF}
                END_REF=`expr ${START_REF} + ${NUM_REF} - 1`

                CURR_NE=${START_NE}
                END_NE=`expr ${START_NE} + ${NUM_NE} - 1`

                while [ ${CURR_REF} -le ${END_REF} ] ; do

                    REF=`printf "%s1%04X" ${MCC_MNC} ${CURR_REF}`
                    NODE=`echo ${MSRBS_V2_NODE_LIST[${CURR_NE} - 1]}`

                    ln -s  ${TMPFS_IN_FILE} ${OUT_ROOT}/${NODE}/${FILE_PATH}/A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF}.bin.gz

                    CURR_REF=`expr ${CURR_REF} + 1`
                    CURR_NE=`expr ${CURR_NE} + 1`
                    if [ ${CURR_NE} -gt ${END_NE} ] ; then
                        CURR_NE=${START_NE}
                    fi
                done
            fi
        done
    fi

    if [ ! -z "${NRAT_NODE_LIST}" ] ; then

        for LTE_UETRACE in ${NRAT_LTE_UETRACE_LIST}; do

            UETRACE_SIM=`echo ${LTE_UETRACE} | awk -F: '{print $2}'`

            MY_SIM_ID=$(echo ${MY_SIM} | rev | awk -F'-' '{print $1}' | rev )

                if [[ "${UETRACE_SIM}" == "${MY_SIM_ID}" ]]; then

                    LRAT_FILE_PATH="//"

                    NRAT_FILE_PATH=$(python ${COMMUNICATOR_PY} 1 "${MY_SIM}")

                    if [[ $? -ne 0 ]]; then
                            return
                    fi

                FILE_PATH="${NRAT_FILE_PATH}"

                if [[ "${SIM_BEHAVIOUR}" == "MixedNRAT" ]]; then
                    FILE_PATH="${LRAT_FILE_PATH} ${NRAT_FILE_PATH}"
                fi

                NODE_COUNT_IN_ARRAY=${#NRAT_NODE_LIST[@]}

                UE_COUNT=0
                if [[ ${ROP_PERIOD_MIN} -eq 1 ]]; then
                        UE_COUNT=${NRAT_ONE_MIN_UE_COUNT}
                elif [[ ${ROP_PERIOD_MIN} -eq 15 ]]; then
                UE_COUNT=${NRAT_FIFTEEN_MIN_UE_COUNT}
                else
                    return
                fi

                UETRACE_FILE=`echo ${LTE_UETRACE} | awk -F: '{print $1}'`

                IN_FILE_PATH="${REC_TEMPLATE_DIR}/${UETRACE_FILE}"
                TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${UETRACE_FILE}"

                if [ ! -r ${IN_FILE_PATH} ] ; then
                   log "ERROR: Cannot find ${IN_FILE_PATH}"
                   exit 1
                else
                   if [ ! -r ${TMPFS_IN_FILE} ] ; then
                      copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                   fi
                fi

                START_NE=`echo ${LTE_UETRACE} | awk -F: '{print $3}'`
                NUM_NE=`echo ${LTE_UETRACE} | awk -F: '{print $4}'`
                END_NE=`expr ${START_NE} + ${NUM_NE} - 1`

                if [[ ${NODE_COUNT_IN_ARRAY} -lt ${END_NE} ]]; then
                    END_NE=${NODE_COUNT_IN_ARRAY}
                    if [[ ${END_NE} -lt ${START_NE} ]]; then
                        START_NE=${END_NE}
                    fi
                fi

                START_REF=`echo ${LTE_UETRACE} | awk -F: '{print $5}'`
                CURR_REF=${START_REF}

                manifest_file_name="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_Trace.manifest"

                for (( NE=${START_NE}; NE <= ${END_NE}; NE++ )); do
                    node=$(echo ${NRAT_NODE_LIST[${NE} - 1]})
                    if grep -q ${node} "/tmp/showstartednodes.txt"; then
                        for ue_pm_path in ${FILE_PATH}; do
                            node_dir_path="${OUT_ROOT}/${node}${ue_pm_path}"
                            CURR_REF=${START_REF}
                            for (( ue_index=1; ue_index <= ${UE_COUNT}; ue_index++ )); do
                                REF=`printf "%s1%04X" ${MCC_MNC_3GPP} ${CURR_REF}`
                                REF_LTE=`printf "%s1%04X" ${MCC_MNC} ${CURR_REF}`
                                if [[ "${ue_pm_path}" == "//" ]]; then
                                    link_file="${node_dir_path}/A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF_LTE}.bin.gz"
                                    if [[ ! -f "${link_file}" ]]; then
                                        ln -s ${TMPFS_IN_FILE}  ${node_dir_path}/A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF_LTE}.bin.gz
                                    fi
                                else
                                    net_fun=$(basename ${ue_pm_path} | rev | awk -F'_' '{print $1}' | rev )
                                    if [[ ${net_fun} == "CUCP" ]]; then
                                        net_fun_file_name="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}-${net_fun}${UE_CUCP_INSTANCE_VALUE}_uetrace_${REF}.gpb.gz"
                                    elif [[ ${net_fun} == "CUUP" ]]; then
                                        net_fun_file_name="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}-${net_fun}${UE_CUUP_INSTANCE_VALUE}_uetrace_${REF}.gpb.gz"
                                    elif [[ ${net_fun} == "DU" ]]; then
                                        net_fun_file_name="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}-${net_fun}${UE_DU_INSTANCE_VALUE}_uetrace_${REF}.gpb.gz"
                                    else
                                        net_fun_file_name="A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}-${net_fun}_uetrace_${REF}.gpb.gz"
                                    fi
                                    link_file="${node_dir_path}/${net_fun_file_name}"
                                    if [[ ! -f "${link_file}" ]]; then
                                        ln -s ${TMPFS_IN_FILE} ${node_dir_path}/${net_fun_file_name}
                                        echo "./${net_fun_file_name}" >> ${node_dir_path}/${manifest_file_name}
                                    fi
                                fi
                                CURR_REF=`expr ${CURR_REF} + 1`
                            done
                        done
                    fi
                    START_REF=`expr ${START_REF} + ${UE_COUNT}`
                done
            fi
        done
    fi


    if [ ! -z "${MSRBS_V1_NODE_LIST}" ] ; then
        # removed as per https://jira-nam.lmera.ericsson.se/browse/NSS-6488
        #if [ -z "${MSRBS_V1_LTE_UETRACE_LIST}" ] ; then
        #    log "ERROR: MSRBS_V1_LTE_UETRACE_LIST not set"
        #    exit 1
        #fi

        FILE_PATH="//"
        if [ ! -z "${MSRBS_V1_PMEvent_FileLocation}" ] ; then
            FILE_PATH=${MSRBS_V1_PMEvent_FileLocation}
        fi

        if [ ${#pERBS_NODE_LIST[@]} -eq 0 ] ; then
            log "WARN: pERBS nodes are not available in ${SIM} simulation."
            return
        fi

        #
        # UETrace
        #
        for LTE_UETRACE in ${MSRBS_V1_LTE_UETRACE_LIST} ; do
            UETRACE_SIM=`echo ${LTE_UETRACE} | awk -F: '{print $2}'`
            if [ "${UETRACE_SIM}" = "${MY_SIM}" ] ; then
                UETRACE_FILE=`echo ${LTE_UETRACE} | awk -F: '{print $1}'`
                START_NE=`echo ${LTE_UETRACE} | awk -F: '{print $3}'`
                NUM_NE=`echo ${LTE_UETRACE} | awk -F: '{print $4}'`
                START_REF=`echo ${LTE_UETRACE} | awk -F: '{print $5}'`
                NUM_REF=`echo ${LTE_UETRACE} | awk -F: '{print $6}'`

                IN_FILE_PATH="${REC_TEMPLATE_DIR}/${UETRACE_FILE}"
                TMPFS_IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${UETRACE_FILE}"

                if [ ! -r ${IN_FILE_PATH} ] ; then
                    log "ERROR: Cannot find ${IN_FILE_PATH}"
                    exit 1
                else
                    if [ ! -r ${TMPFS_IN_FILE} ] ; then
                     copySourceTemplates ${IN_FILE_PATH} ${TMPFS_IN_FILE}
                    fi
                fi

                if [ ${#pERBS_NODE_LIST[@]} -lt ${NUM_NE} ]; then
                    NUM_NE=${#pERBS_NODE_LIST[@]}
                fi

                CURR_REF=${START_REF}
                END_REF=`expr ${START_REF} + ${NUM_REF} - 1`

                CURR_NE=${START_NE}
                END_NE=`expr ${START_NE} + ${NUM_NE} - 1`

                while [ ${CURR_REF} -le ${END_REF} ] ; do

                    REF=`printf "%s1%04X" ${MCC_MNC} ${CURR_REF}`
                    NODE=`echo ${pERBS_NODE_LIST[${CURR_NE} - 1]}`

                    ln -s ${TMPFS_IN_FILE} ${OUT_ROOT}/${NODE}/${FILE_PATH}/A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF}.bin.gz

                    CURR_REF=`expr ${CURR_REF} + 1`
                    CURR_NE=`expr ${CURR_NE} + 1`
                    if [ ${CURR_NE} -gt ${END_NE} ] ; then
                        CURR_NE=${START_NE}
                    fi
                done
            fi
        done
    fi

    if [ ! -z "${VTF_NODE_LIST}" ] ; then

        VTF_FILE_PATH="//"
        if [ ! -z "${VTFRADIONODE_PMEvent_FileLocation}" ] ; then
            VTF_FILE_PATH=${VTFRADIONODE_PMEvent_FileLocation}
        fi

        for VTF_UETRACE in ${VTF_UETRACE_LIST} ; do
            UETRACE_SIM=`echo ${VTF_UETRACE} | awk -F: '{print $2}'`
            if [[ $MY_SIM == *"-VTFR"* ]]; then
                UETRACE_FILE=`echo ${VTF_UETRACE} | awk -F: '{print $1}'`
                START_NE=`echo ${VTF_UETRACE} | awk -F: '{print $3}'`
                NUM_NE=`echo ${VTF_UETRACE} | awk -F: '{print $4}'`
                START_REF=`echo ${VTF_UETRACE} | awk -F: '{print $5}'`
                NUM_REF=`echo ${VTF_UETRACE} | awk -F: '{print $6}'`

                if [[ ${VTF_NODE_COUNT} -gt 0 ]]; then
                    NUM_NE=${VTF_NODE_COUNT}
                    NUM_REF=$((${NUM_NE} * 16))
                fi

                IN_FILE_PATH="${REC_TEMPLATE_DIR}/${UETRACE_FILE}"
                if [ ! -r ${IN_FILE_PATH} ] ; then
                    log "ERROR: Cannot find ${IN_FILE_PATH}"
                    exit 1
                fi

                if [ ${#VTF_NODE_LIST[@]} -lt ${NUM_NE} ]; then
                    NUM_NE=${#VTF_NODE_LIST[@]}
                fi

                CURR_REF=${START_REF}
                END_REF=`expr ${START_REF} + ${NUM_REF} - 1`

                CURR_NE=${START_NE}
                END_NE=`expr ${START_NE} + ${NUM_NE} - 1`

                while [ ${CURR_REF} -le ${END_REF} ] ; do

                    REF=`printf "%s1%04X" ${MCC_MNC} ${CURR_REF}`
                    NODE=`echo ${VTF_NODE_LIST[${CURR_NE} - 1]}`

                    ln -s ${IN_FILE_PATH} ${OUT_ROOT}/${NODE}/${VTF_FILE_PATH}/A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}_uetrace_${REF}.bin.gz

                    CURR_REF=`expr ${CURR_REF} + 1`
                    CURR_NE=`expr ${CURR_NE} + 1`
                    if [ ${CURR_NE} -gt ${END_NE} ] ; then
                        CURR_NE=${START_NE}
                    fi
                done
            fi
        done
    fi
}

# ebs file generation
updateEBSTemplates() {

    CURR_ROP=${ROP_START_TIME_LOCAL}
    STARTTIME="${ROP_START_DATE_LOCAL}.${ROP_START_TIME_LOCAL}"
    ENDTIME="${ROP_END_DATE_LOCAL}.${ROP_END_TIME_LOCAL}"

    STARTTIME_STR=`echo "$STARTTIME" | sed 's/\(....\)\(..\)\(..\)\.\(..\)\(..\)/\1 \2 \3 \4 \5/'`
    YEAR=`echo ${STARTTIME_STR} | awk '{print $1}'`
    MON=`echo ${STARTTIME_STR} | awk '{print $2}'`
    MON=${MON#0}
    DAY=`echo ${STARTTIME_STR} | awk '{print $3}'`
    DAY=${DAY#0}
    HOUR=`echo ${STARTTIME_STR} | awk '{print $4}'`
    HOUR=${HOUR#0}
    MIN=`echo ${STARTTIME_STR} | awk '{print $5}'`
    MIN=${MIN#0}
    SEC="00"

    DIR=`cat ${MME_REF_CFG} | awk -F':' '{print $3}' | sort -u`

    if [ -d "$DIR" ] ; then
        FILES=`ls $DIR | grep "A.\{8\}\.${CURR_ROP}"`
        if [ -z "$FILES" ] ; then
            echo "ERROR : No reference files found under $DIR for ROP ${STARTTIME}"
        else
                for FILE in $FILES  ; do
                NEWFILE=`echo $FILE | sed "s/A.............\(.....\)-..................\(.*$\)/A${STARTTIME}\1-${ENDTIME}\1\2/"`
                #Move old file to new file with current timestamp in filename only
                mv $DIR/$FILE $DIR/$NEWFILE
                #Update current timestamp in new file
                printf "%.4x%.2x%.2x%.2x%.2x%.2x" $YEAR $MON $DAY $HOUR $MIN $SEC | xxd -r -p | dd of=$DIR/$NEWFILE bs=1 count=7 seek=5 conv=notrunc
            done
        fi
        else
        echo "ERROR : Reference EBS file directory not present $DIR"
    fi
}

#Generated the EBS files as per the configuration
#Defined in ME_REF_CFG
makeEBS() {

    SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"

    while read LINE ; do
        if [ ! -z "$LINE" ] ; then
            SIM=`echo ${LINE} | awk -F: '{print $1}'`
            NODE=`echo ${LINE} | awk -F: '{print $2}'`
            FILE_SET=`echo ${LINE} | awk -F: '{print $3}'`
            if [ -d "${FILE_SET}" ] ; then
                NODE_DIR="${SIM_DIR}/${SIM}/${NODE}"
                if [ -d "${NODE_DIR}" ] ; then
                    EBS_OUTPUT_DIR="${NODE_DIR}/fs/tmp/OMS_LOGS/ebs/"
                    # Create ebs dir structure if not present
                    if [ -d "${EBS_OUTPUT_DIR}" ] ; then
                        ls -l ${EBS_OUTPUT_DIR} | grep '^d' | grep ready > /dev/null
                        if [[ $? -eq 0 ]]; then
                            rm -rf ${EBS_OUTPUT_DIR}/ready
                        fi
                        ls -l ${EBS_OUTPUT_DIR} | grep -v '^d' | grep ready > /dev/null
                        if [[ $? -ne 0 ]]; then
                            ln -s ${EBM_SAMPLE_HL} ${EBS_OUTPUT_DIR}/ready
                        fi
                        else
                                mkdir -p ${EBS_OUTPUT_DIR}
                                ln -s ${EBM_SAMPLE_HL} ${EBS_OUTPUT_DIR}/ready
                    fi
                    EBS_FILES=`ls ${FILE_SET} | grep "A${ROP_START_DATE_LOCAL}.${ROP_START_TIME_LOCAL}"`
                    if [ ! -z "${EBS_FILES}" ] ; then
                        for FILE in ${EBS_FILES}  ; do
                            EVENT_FILENAME=`echo $FILE | sed "s/A......................................\(.*$\)/${EBS_FILENAME_PREFIX}\1/"`
                            if [[ ! -f "${EBM_SAMPLE_HL}/${EVENT_FILENAME}" ]]; then
                                 ln "${FILE_SET}/${FILE}" "${EBM_SAMPLE_HL}/${EVENT_FILENAME}"
                            fi
                        done
                    else
                        echo "ERROR : No reference files found under ${FILE_SET} for ROP ${STARTTIME} for the Node : $NODE "
                    fi
                else
                    echo "ERROR : Invalid NODE/SIM, ${NODE_DIR} not present for Node : $NODE"
                fi
            else
                echo "ERROR : Reference EBS file directory ${FILE_SET}  not present for Node : $NODE"
            fi
        fi
    done < "${MME_REF_CFG}"
}


generateCTUM() {

    # Get last ROP UETRACE file index
    CTUM_INDEX=`cat "${REC_TEMPLATE_DIR}/.ctum"`

    if [ -z "${MME_CTUM_LIST}" ] ; then
        log "WRAN: MME_CTUM_LIST not found or empty. MME CTUM files will be not be generated"
    else
        CTUM_INDEX=`expr ${CTUM_INDEX} + 1`
    fi

    SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"

    for SIM in ${MME_SIM_LIST}  ; do

        echo `ls ${SIM_DIR}` | grep ${SIM} > /dev/null

        if [ $? -eq 0 ] ; then

            # Get the NE List
            NE_LIST=`ls ${OUT_ROOT}`
            if [[ ${EXEC_FROM_HC} == "YES" ]]; then
               echo "ctum"
               echo $NE_LIST
            fi
            for NE in ${NE_LIST}; do

                if [ ! -z "${MME_CTUM_LIST}" ] ; then

                    CTUM_OUTPUTDIR="${OUT_ROOT}/${NE}/tmp/OMS_LOGS/ctum/ready/"
                    CTUM_NODEDIR="${SIM_DIR}/${SIM}/${NE}/fs/tmp/OMS_LOGS/ctum/ready/"
                    #Create ctum dir structure if not present
                    if [[ ! -d ${CTUM_OUTPUTDIR} ]];then
                        echo $CTUM_OUTPUTDIR
                        echo $CTUM_NODEDIR
                        createOutputDir ${CTUM_OUTPUTDIR} ${CTUM_NODEDIR}
                    fi
                    for MME_CTUM in ${MME_CTUM_LIST} ; do

                        IN_FILE_NAME=`echo ${MME_CTUM} | awk -F: '{print $1}'`
                        ROP_INDEX=`echo ${MME_CTUM} | awk -F: '{print $2}'`

                        SOURCE_CTUM_FILE="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
                        IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${IN_FILE_NAME}"
                        OUT_FILE_NAME="${MME_CTUM_FILENAME_PREFIX}${ROP_INDEX}_ctum.${CTUM_INDEX}"

                        if [ ! -r ${IN_FILE} ] ; then
                            if [ -r ${SOURCE_CTUM_FILE} ] ; then
                                copySourceTemplates ${SOURCE_CTUM_FILE} ${IN_FILE}
                            else
                                log "ERROR: Cannot find ${SOURCE_CTUM_FILE}"
                                exit 1
                            fi
                        fi
                        ln "${IN_FILE}" "${CTUM_OUTPUTDIR}/${OUT_FILE_NAME}"
                    done
                fi
            done
        fi
    done

    # Persist rop index value for ctum fiels
    echo ${CTUM_INDEX} > "${REC_TEMPLATE_DIR}/.ctum"

}


generateMMEUETRACE() {

    # Get last ROP UETRACE  file index
    UETRACE_INDEX=`cat "${REC_TEMPLATE_DIR}/.uetrace"`

    if [ -z "${MME_UETRACE_LIST}" ] ; then
        log "WRAN: MME_UETRACE_LIST not found or empty. MME UETRACE files will be not be generated"
    else
        UETRACE_INDEX=`expr ${UETRACE_INDEX} + 1`
    fi


    SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"

    for SIM in ${MME_SIM_LIST}  ; do

        echo `ls ${SIM_DIR}` | grep ${SIM} > /dev/null
        if [ $? -eq 0 ] ; then
            # Get the NE List
            NE_LIST=`ls ${OUT_ROOT}`
            if [[ ${EXEC_FROM_HC} == "YES" ]]; then
               echo "uetrace"
               echo $NE_LIST
            fi
            for NE in $NE_LIST; do
                if [ ! -z "${MME_UETRACE_LIST}" ] ; then
                    UETRACE_OUTPUTDIR="${OUT_ROOT}/${NE}/tmp/OMS_LOGS/ue_trace/ready"
                    UETRACE_NODEDIR="${SIM_DIR}/${SIM}/${NE}/fs/tmp/OMS_LOGS/ue_trace/ready"
                    # Create uetrace dir structure if not present
                    if [[ ! -d ${UETRACE_OUTPUTDIR} ]];then
                        echo $UETRACE_OUTPUTDIR
                        echo $UETRACE_NODEDIR
                        createOutputDir ${UETRACE_OUTPUTDIR} ${UETRACE_NODEDIR}
                    fi
                    for MME_UETRACE in ${MME_UETRACE_LIST} ; do

                        IN_FILE_NAME=`echo ${MME_UETRACE} | awk -F: '{print $1}'`
                        FILE_VER=`echo ${MME_UETRACE} | awk -F: '{print $2}'`
                        ROP_INDEX=`echo ${MME_UETRACE} | awk -F: '{print $3}'`

                        SOURCE_MME_UETRACE_FILE="${REC_TEMPLATE_DIR}/${IN_FILE_NAME}"
                        IN_FILE="${TMPFS_REC_TEMPLATES_DIR}/${IN_FILE_NAME}"
                        OUT_FILE_NAME="${MME_UETRACE_FILENAME_PREFIX}-MME.${NE}.${FILE_VER}_${ROP_INDEX}_ue_trace.${UETRACE_INDEX}"

                        if [ ! -r ${IN_FILE} ] ; then
                            if [ -r ${SOURCE_MME_UETRACE_FILE} ] ; then
                                copySourceTemplates ${SOURCE_MME_UETRACE_FILE} ${IN_FILE}
                            else
                                log "ERROR: Cannot find ${SOURCE_MME_UETRACE_FILE}"
                                exit 1
                            fi
                        fi
                        ln "${IN_FILE}" "${UETRACE_OUTPUTDIR}/${OUT_FILE_NAME}"
                    done
                fi

            done
        fi
    done
    # Persist rop index value for uetrace fiels
    echo ${UETRACE_INDEX} > "${REC_TEMPLATE_DIR}/.uetrace"

}


generateEBS() {

   if [[ "${REAL_NODE_EBM_DATA}" == "true" ]] ; then
        makeEBS
    else
        if [ -z "${MME_EBS_FILE_LIST}" ] ; then
            log "ERROR: MME_EBS_FILE_LIST variable is empty or not present in /netsim/netsim_cfg"
        fi
    fi


   if [[  ${TYPE} == "MD_1" ]];then
    if [[ ${ROP_PERIOD_MIN} == '15' ]];then
       MME_EBS_FILE_LIST=` echo $MME_EBS_FILE_LIST | awk -F' ' '{print $2}' |awk -F':' '{print $2}'| sed 's/,/ /g'`
    elif [[  ${ROP_PERIOD_MIN} == '1' ]];then
        MME_EBS_FILE_LIST=`echo $MME_EBS_FILE_LIST | awk -F' ' '{print $1}' |awk -F':' '{print $2}' | sed 's/,/ /g'`
    fi
   fi
    # Get last ROP EBS file index
    EBS_FILE_INDEX=`cat "${REC_TEMPLATE_DIR}/.ebs_${ROP_PERIOD_MIN}"`

    SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"

    FILE_INDEX=1;

    for SIM in ${MME_SIM_LIST}  ; do
        echo `ls ${SIM_DIR}` | grep ${SIM} > /dev/null
        if [ $? -eq 0 ] ; then
            # Get the NE List
            NE_LIST=`ls ${OUT_ROOT}`
            for NE in $NE_LIST; do
                if [ "${REAL_NODE_EBM_DATA}" = "false" ] ; then
                    EBS_OUTPUTFILE="${SIM_DIR}/${SIM}/${NE}/fs/tmp/OMS_LOGS/ebs/"
                    # Create ebs dir structure if not present
                    if [ -d "${EBS_OUTPUTFILE}" ] ; then
                        ls -l ${EBS_OUTPUTFILE} | grep '^d' | grep ready > /dev/null
                        if [[ $? -eq 0 ]]; then
                            rm -rf ${EBS_OUTPUTFILE}/ready
                        fi
                        ls -l ${EBS_OUTPUTFILE} | grep -v '^d' | grep ready > /dev/null
                        if [[ $? -ne 0 ]]; then
                            ln -s ${EBM_SAMPLE_HL} ${EBS_OUTPUTFILE}/ready
                        fi
                    else
                        mkdir -p ${EBS_OUTPUTFILE}
                        ln -s ${EBM_SAMPLE_HL} ${EBS_OUTPUTFILE}/ready
                    fi
                    EBS_FILE_INDEX=`cat "${REC_TEMPLATE_DIR}/.ebs_${ROP_PERIOD_MIN}"`
                    for FILE in ${MME_EBS_FILE_LIST} ; do
                        EVENT_FILENAME="${EBS_FILENAME_PREFIX}${FILE_INDEX}_ebs"
                        IN_FILE="${EBM_SAMPLE_TEMP}/${FILE}"
                        if [ ! -r ${IN_FILE} ] ; then
                            log "ERROR: Cannot find ${IN_FILE}"
                            exit 1
                        fi
                        if [[ ! -f "${EBM_SAMPLE_HL}/${EVENT_FILENAME}.${EBS_FILE_INDEX}" ]]; then
                            ln "${IN_FILE}" "${EBM_SAMPLE_HL}/${EVENT_FILENAME}.${EBS_FILE_INDEX}"
                        fi
                        EBS_FILE_INDEX=`expr ${EBS_FILE_INDEX} + 1`
                        FILE_INDEX=`expr ${FILE_INDEX} + 1`
                    done
                    # Reset EBS file index
                    FILE_INDEX=1;
                fi
            done
        fi
    done

    #Total file per day = 8 * 4 * 24 = 768 after that reset the value

    TOTAL_FILES_PER_DAY=`expr ${FILE_INDEX} \* 60 \/ ${ROP_PERIOD_MIN}  \* 24`
    if [[ ${EBS_FILE_INDEX} -ge ${TOTAL_FILES_PER_DAY} ]] ; then
        EBS_FILE_INDEX=1
    fi
    # Persist EBS file index value
    echo ${EBS_FILE_INDEX} > "${REC_TEMPLATE_DIR}/.ebs_${ROP_PERIOD_MIN}"
}


# For MME sims /pms_tmpfs path will not be used
processMMESim() {

    if [[ "${EBM_GEN_CHECK}" == "true" ]] ; then
        #echo "Generating EBS files"
        generateEBS
    fi

    echo "${FILE_TYPES}" | egrep -w "ALL|UETRACE" > /dev/null
    if [ $? -eq 0 ] ; then
        #echo "Generating MME UETRACE files"
        generateMMEUETRACE
    fi

    echo "${FILE_TYPES}" | egrep -w "ALL|CTUM" > /dev/null
    if [ $? -eq 0 ] ; then
        #echo "Generating CTUM files"
        generateCTUM
    fi
}

# This method call python script which generate celltrace for simulation which has configurable parameter
generateCelltraceForConfSims(){
    log "INFO: Caling ${CONF_CELLTRACE_SCRIPT} ${DATE} ${ROP_START_TIME} ${ROP_END_TIME} ${epoch_rop}"
    python ${CONF_CELLTRACE_SCRIPT} ${DATE} ${ROP_START_TIME} ${ROP_END_TIME} ${epoch_rop} >> /netsim_users/pms/logs/confCelltrace.log
}

log "Start ${ROP_START_TIME}"

EBM_GEN_CHECK="false"
REAL_NODE_EBM_DATA="false"
EBM_SAMPLE_HL="/store/EBM_HardLink/"
EBM_SAMPLE_TEMP="/store/EBM_Sample_Templates/"
CONF_CELLTRACE_SCRIPT="/netsim_users/auto_deploy/bin/generateConfigurableCelltrace.py"
COMMUNICATOR_PY="/netsim_users/auto_deploy/bin/shellToPythonCommunicator.py"

if [[ ${CELLTRACE_ENABLED} !=  "true" ]]; then
    log "INFO : Celltrace is not enabled in netsim_cfg, exiting..."
    exit 1
fi

for SIM in $LIST ; do
    if grep -q $SIM "/tmp/showstartednodes.txt"; then
        SIM_TYPE=`getSimType ${SIM}`
        SIM_BEHAVIOUR=$(cat ${SIM_TYPE_FILE} | grep "${SIM}:" | awk -F':' '{print $3}')
        if [[ ${TYPE} == "DO" && ${SIM_TYPE} == "GNODEBRADIO" ]];then
            continue
        elif [ "${SIM_TYPE}" = "LTE" ] || [ "${SIM_TYPE}" = "VTFRADIONODE" ] || [ "${SIM_TYPE}" = "GNODEBRADIO" ]; then
            processSim ${SIM}
        elif [ "${SIM_TYPE}" = "WRAN" ] ; then
            MY_HAS_LTE=$(eval "echo \$$(echo ${SIM}_HAS_LTE)")
            if [ ! -z "${MY_HAS_LTE}" ] && [ ${MY_HAS_LTE} -eq 1 ] ; then
                processSim $SIM
            fi
        fi
    fi
done


# Process SGSN simulation if any
if [ ! -z "${MME_SIM_LIST}" ] ; then
        echo "${FILE_TYPES}" | egrep -w "ALL|EBM|EBS" > /dev/null
    if [[ $? -eq 0 ]] && [[ -f ${MME_REF_CFG} ]]; then

         if [[ ${ROP_PERIOD_MIN} -eq 1  ]] || [[ ${ROP_PERIOD_MIN} -eq 15 && ${TYPE} == "MD_1" ]]; then
                cfg_line=$(cat ${MME_REF_CFG} | head -1 | awk -F: '{print $3}' | sed 's/ //g')
            if [[ ! -z "${cfg_line}" ]] && [[ -d "${cfg_line}" ]]; then
                EBM_GEN_CHECK="true"
                if [[ "${cfg_line}" == *"HSTNTX01LT9"* ]]; then
                    REAL_NODE_EBM_DATA="true"
                    firstDir=$(echo ${cfg_line} | awk -F'/' '{print $2}')
                    EBM_SAMPLE_HL="/${firstDir}/EBM_HardLink/"
                    EBM_SAMPLE_TEMP="/${firstDir}/EBM_Sample_Templates/"
                    updateEBSTemplates
                fi
            else
                echo "ERROR: Data path not proper in ${MME_REF_CFG} file."
            fi
        fi
    else
        echo "WARNING: Cron is not set for EBM or ${MME_REF_CFG} file not available."
    fi
    processMMESim
fi

log "INFO : LTE 4G CellTrace generation has been completed."

echo "${FILE_TYPES}" | egrep -w "ALL|CELLTRACE" > /dev/null
if [ $? -eq 0 ] ; then
    if [[ $TYPE != "DO" ]];then
       log "INFO : Generating NR CellTrace..."
       generateCelltraceForConfSims
       log "INFO : NR CellTrace has been generated."
    else
       log "INFO: CELLTRACE FILE HANDLING NOT NEEDED  in $TYPE"
    fi
fi

touch_epoch_format=$(echo ${epoch_rop} | sed 's/_/|/g')
touch "/netsim_users/pms/config/touch_files/${touch_epoch_format},CELLTRACE"
log "End ${ROP_START_TIME}"
