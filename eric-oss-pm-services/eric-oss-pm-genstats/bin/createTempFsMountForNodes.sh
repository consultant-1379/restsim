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
# Version no    :  NSS 22.13
# Purpose       :  Script creates and mounts real node file path if configured for any node type.
# Jira No       :  NSS-40224 
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/12930329
# Description   :  Fixing self mounting issue
# Date          :  20/07/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

# XSURJAJ
#
# This script is responsible to create PM and PMEVENT file location directories
# under Node file system and temp file system including mount binding between them
#
#

. /netsim/netsim_cfg > /dev/null 2>&1

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`

. ${BIN_DIR}/functions

SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"
#OUT_ROOT="/pms_tmpfs"
OUT_ROOT="/ericsson/pmic1/XML"

if [ -z "${EPG_PM_FileLocation}" ] ; then
     EPG_PM_FileLocation="/var/log/services/epg/pm/"
fi
mount_logs='/netsim_users/pms/logs/mount.log'

# Create mount binding between node file system
# temp file system
createMount() {

    SIM=$1
    FILE_PATH=$2
    SIM_TYPE=$3
    SIM_NAME=''

    if [[ ${SIM_TYPE} == LTE || ${SIM_TYPE} == WRAN ]];then
        SIM_NAME=`ls ${SIM_DIR} | grep -i "\-${SIM}" `
    else
        SIM_NAME=`ls ${SIM_DIR} | grep -w ${SIM} `
    fi

    if [ $? -eq 0 ] ; then

        NODE_LIST=`ls ${SIM_DIR}/${SIM_NAME}`
        if [ "${SIM_TYPE}" = "EPG-SSR" ]; then
           echo "$(date) nodeslist of epg-ssr : $NODE_LIST " >> $mount_logs
        fi
        for NODE in ${NODE_LIST} ; do

            if ! grep -q ${NODE} "/tmp/showstartednodes.txt"; then
                continue
            fi
            if [ "${SIM_TYPE}" = "EPG-SSR" ]; then
               echo "$(date) started node : $NODE " >> $mount_logs
            fi
            NODE_PATH="${SIM_DIR}/${SIM_NAME}/${NODE}/fs/${FILE_PATH}"
            NODE_TEMP_PATH="${OUT_ROOT}/${NODE}/${FILE_PATH}"
            
            umount -f -l "${NODE_PATH}"
            if [ $? -ne 0 ]; then
                echo "Warning: Unable to force umount or mounting does not exist : ${NODE_PATH} " >> $mount_logs
            fi            
            rm -rf "${NODE_PATH}"
            mkdir -p "${NODE_PATH}"
            chown -R netsim:netsim "${SIM_DIR}/${SIM_NAME}/${NODE}/fs"
            mkdir -p "${NODE_TEMP_PATH}"
            chown -R netsim:netsim "${OUT_ROOT}/${NODE}"              
            mount -B ${NODE_TEMP_PATH} ${NODE_PATH}
            mount -a
        done
    else
        log " $SIM not found"
    fi
}


createCustomizedMountingPoint(){
    umount -f -l "${dest_path}"
    if [ $? -ne 0 ]; then
        echo "Warning: Unable to force umount or mounting does not exist : ${dest_path} " >> $mount_logs
    fi 
    rm -rf "${dest_path}"
    mkdir -p "${dest_path}"
    chown -R netsim:netsim "${dest_path}"
    chown -R netsim:netsim "${src_path}"
    echo "$(date) pm_tmpfs path : $src_path" >> $mount_logs
    echo "$(date) netsimdbdir path : $dest_path" >> $mount_logs
    mount -B ${src_path} ${dest_path}
    mount -a
}


createTempFsMounting() {

   log "createTempFsMountForNodes start"

   if [[ ! -z ${src_path} ]] && [[ ! -z ${dest_path} ]]; then
       createCustomizedMountingPoint
       exit 0
   fi

   for SIM in $LIST ; do
        if grep -q $SIM "/tmp/showstartednodes.txt"; then

        NODE_TYPE=""

        SIM_TYPE=`getSimType ${SIM}`

        if [ "${SIM_TYPE}" = "WRAN" ] || [ "${SIM_TYPE}" = "RBS" ] ; then

            #Check for DG2 nodes
            MSRBS_V2_LIST=`ls ${OUT_ROOT}/ | grep MSRBS-V2`
            #Check for PRBS nodes
            PRBS_LIST=`ls ${OUT_ROOT}/ | grep PRBS`
            #Check for RBS nodes
            RBS_LIST=`ls ${OUT_ROOT}/ | grep RBS`
            if [ ! -z "${MSRBS_V2_LIST}" ] ; then
                NODE_TYPE="MSRBS_V2"
            elif [ ! -z "${PRBS_LIST}" ] ; then
                NODE_TYPE="PRBS"
            elif [ ! -z "${RBS_LIST}" ] ; then
                NODE_TYPE="RBS"
            else
                NODE_TYPE="RNC"
            fi

        elif [ "${SIM_TYPE}" = "LTE" ] ; then
            MSRBS_V1_LIST=`ls ${OUT_ROOT}/ | grep pERBS`
            MSRBS_V2_LIST=`ls ${OUT_ROOT}/ | grep dg2ERBS`
            if [ ! -z "${MSRBS_V1_LIST}" ] ; then
                NODE_TYPE="MSRBS_V1"
            elif [ ! -z "${MSRBS_V2_LIST}" ] ; then
                NODE_TYPE="MSRBS_V2"
            fi

        elif [ "${SIM_TYPE}" = "TCU04" ] || [ "${SIM_TYPE}" = "C608" ] ; then
            NODE_TYPE="TCU04"
        elif [ "${SIM_TYPE}" = "TCU03" ] ; then
            NODE_TYPE="TCU"
        elif [ "${SIM_TYPE}" = "GSM_DG2" ] ; then
            NODE_TYPE="MSRBS_V2"
        elif [ "${SIM_TYPE}" = "HSS" ] ; then
            NODE_TYPE="HSS_FE"
        elif [ "${SIM_TYPE}" = "EPG-SSR" ] || [ "${SIM_TYPE}" = "EPG-EVR" ]; then
            NODE_TYPE="EPG"
        elif [ "${SIM_TYPE}" = "VBGF" ] ; then
            NODE_TYPE="MRSV"
        elif [ "${SIM_TYPE}" = "MRF" ] ; then
            NODE_TYPE="MRFV"
        elif [ "${SIM_TYPE}" = "5GRADIONODE" ] ; then
            NODE_TYPE="FIVEGRADIONODE"
        elif [ "${SIM_TYPE}" = "SHARED-CNF" ] ; then
            NODE_TYPE="SHARED_CNF"
        else
            NODE_TYPE="${SIM_TYPE}"
        fi

        # For STATS
        ne_file_location="${NODE_TYPE}"_PM_FileLocation
        PMDIR=${!ne_file_location}

        if [ ! -z "${PMDIR}" ] ; then
            createMount "${SIM}" "${PMDIR}" "${SIM_TYPE}"
        fi

        # For EVENTS
        ne_file_location="${NODE_TYPE}"_PMEvent_FileLocation
        PMDIR=${!ne_file_location}

        if [ ! -z "${PMDIR}" ] ; then
            createMount "${SIM}" "${PMDIR}" "${SIM_TYPE}"
        fi
        fi
    done
    log "createTempFsMountForNodes end"
}

src_path=$1
dest_path=$2

createTempFsMounting
