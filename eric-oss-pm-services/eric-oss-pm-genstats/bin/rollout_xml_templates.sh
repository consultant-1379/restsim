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
# Purpose       :  Script to copy the templates on Netsim server for the simulations configured in netsim_cfg
# Jira No       :  NSS-35517
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/11675757/
# Description   :  Adding 20mb file support for SCEF in MD_1
# Date          :  29/01/2022
# Last Modified :  vadim.malakhovski@tcs.com
#################################################### 

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

NETSIM_PMS_DIR=/netsim_users/pms/
NETSIM_XML_TEMPLATE_DIR=/netsim_users/pms/xml_templates
NETSIM_SANDBOX_TEMPLATE_DIR=/netsim_users/pms/sandbox_templates/
GENSTATS_BCP_TEMPLATE_DIR=/netsim/genstats/bcp_templates
GENSTATS_MINILINK_TEMPLATE_DIR=/netsim/genstats/minilink_templates
GENSTATS_SANDBOX_TEMPLATE_DIR=/netsim/genstats/sandbox_templates
GENSTATS_EPG_TEMPLATE_DIR=/netsim/genstats/epg_templates_NRM3
GENSTATS_EPG_XML_STEP_DIR=/pms_tmpfs/xml_step/epg_templates_NRM3
GENSTATS_SANDBOX_NRM3_TEMPLATE_DIR=/netsim/genstats/sandbox_templates_NRM3
TMPFS_PLAYBACKER_NODES="ECEE EPG-OI vEPG-OI WMG-OI vWMG-OI gNodeBRadio SBG-IS FrontHaul-6020 FrontHaul-6080 vCU-UP vCU-CP vAFG ADP SCEF"
TMPFS_SANDBOX_DIR=/pms_tmpfs/xml_step/sandbox_templates/
TMPFS_XML_TEMPLATES_DIR=/pms_tmpfs/xml_step/xml_templates/
SENT_LIST=""

sendTemplate() {

    THE_SRC=$1
    THE_SERVER=$2
    TARGET_FILE=$3
    ROP_PERIOD=$4
    SRC_FILE=`basename ${THE_SRC}`

    # Check if we've already sent this file
    echo "${SENT_LIST}" | grep -w "${ROP_PERIOD}_${TARGET_FILE}" > /dev/null
    if [ $? -eq 0 ] ; then
        log "INFO:   Already sent ${SRC_FILE} => ${TARGET_FILE}"
        return
    fi

    log "INFO:   Sending ${SRC_FILE} => ${TARGET_FILE}"

    THE_DEST="${NETSIM_XML_TEMPLATE_DIR}/${ROP_PERIOD}/${TARGET_FILE}"

    if [ ! -r "${THE_SRC}" ] ; then
        log "ERROR: Cannot find ${THE_SRC}"
        exit 1
    fi

    /bin/cp ${THE_SRC} ${THE_DEST}

    SRC_DIR=`dirname ${THE_SRC}`
    SRC_FILE=`basename ${THE_SRC} .template`
    SRC_CNTR_PROP="${SRC_DIR}/${SRC_FILE}.cntrprop"
    if [ -r ${SRC_CNTR_PROP} ] ; then
        DEST_DIR=`dirname ${THE_DEST}`
        DEST_FILE=`basename ${THE_DEST} .xml`
        DEST_CNTR_PROP=${DEST_DIR}/${DEST_FILE}.cntrprop
        /bin/cp ${SRC_CNTR_PROP} ${DEST_CNTR_PROP}
    fi

    # To make templates to specific to ROPs as unique entry in SENT_LIST
    SENT_LIST="${SENT_LIST} ${ROP_PERIOD}_${TARGET_FILE}"
}

makeSrcFileName() {

    MY_NE_TYPE=$1
    MY_NE_MIM=$2
    ROP=$3
    JOBID=$4
    TYPE=$5

    MY_NE_MIM=`echo "${MY_NE_MIM}" | sed 's/\./_/g'`

    if [ ! -z ${JOBID} ] ; then
        FILE_NAME=`printf "%s/%s/%s_%s-%s.template" "${XML_TEMPLATE_DIR}" "${ROP}" "${MY_NE_TYPE}" "${MY_NE_MIM}" "${JOBID}"`
    elif [ ! -z ${TYPE} ] ; then
        FILE_NAME=`printf "%s/%s/%s_%s_%s.template" "${XML_TEMPLATE_DIR}" "${ROP}" "${MY_NE_TYPE}" "${MY_NE_MIM}" "${TYPE}"`
    else
        FILE_NAME=`printf "%s/%s/%s_%s.template" "${XML_TEMPLATE_DIR}" "${ROP}" "${MY_NE_TYPE}" "${MY_NE_MIM}"`
    fi
    echo "${FILE_NAME}"
}


getRopIntervals() {

    ROP_PERIOD_LIST=""
    for STATS_WORKLOAD in $STATS_WORKLOAD_LIST; do
        ROP_PERIOD=`echo ${STATS_WORKLOAD} | awk -F: '{print $1}'`
        ROP_PERIOD_LIST="${ROP_PERIOD_LIST} ${ROP_PERIOD}"
    done
    echo "${ROP_PERIOD_LIST}"
}


CONFIGFILE=/netsim/netsim_cfg
PLAYBACK_CONFIGFILE=/netsim_users/pms/bin/playback_cfg

while getopts  "s:c:n:" flag
do
    case "$flag" in

        c) CONFIGFILE="$OPTARG";;
        s) SERVER_LIST="$OPTARG";;
        n) SIM_NAME="$OPTARG";;
        *) printf "Usage: %s < -c configfile > <-s serverlist> < -n simulation_name >\n" $0
           exit 1;;
    esac
done

if [ ! -r ${CONFIGFILE} ] ; then
    log "ERROR: Cannot find ${CONFIGFILE}"
    exit 1
fi
if [ ! -r ${PLAYBACK_CONFIGFILE} ] ; then
    log "ERROR: Cannot find ${PLAYBACK_CONFIGFILE}"
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
. ${PLAYBACK_CONFIGFILE} > /dev/null 2>&1

if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

checkPMDIR
if [ $? -ne 0 ] ; then
    log "ERROR: PMDIR not set correctly"
    exit 1
else
    XML_TEMPLATE_DIR=${PMDIR}/xml_templates
fi

echo ${PLAYBACK_SIM_LIST} | grep -i "SCEF" > /dev/null
if [[ $? == 0 ]];then
   HAS_SCEF=1
fi													  

log "INFO: Reading templates from ${XML_TEMPLATE_DIR}"

for SERVER in ${SERVERS} ; do
    log "INFO: ${SERVER}"


    if [ ! -z "${SIM_NAME}" ] ; then
        LIST=${SIM_NAME}
    else
        log "INFO: Delete old PMS templates"
        #delete old bcp_template directory and copy new one if transport node present in /netsim/netsimdir/
        log "INFO: Deleting old bcp_template directory"
        #/usr/bin/rsh -l netsim ${SERVER} "rm -rf ${NETSIM_PMS_DIR}bcp_templates > /dev/null 2>&1"
        `rm -rf ${NETSIM_PMS_DIR}bcp_templates > /dev/null 2>&1`

        #delete old minilink_template directory and copy new if minilink node present in /netsim/netsimdir/
        log "INFO: Deleting old minilink_template directory"
        #/usr/bin/rsh -l netsim ${SERVER} "rm -rf ${NETSIM_PMS_DIR}minilink_templates > /dev/null 2>&1"
        `rm -rf ${NETSIM_PMS_DIR}minilink_templates > /dev/null 2>&1`
        log "INFO: Sending minilink_templates"
        /bin/cp -r ${GENSTATS_MINILINK_TEMPLATE_DIR} ${NETSIM_PMS_DIR}

        SERVER_NAME=`echo $SERVER | sed s/-/_/g`

        LIST=${LIST}
        #delete any old templates
        #/usr/bin/rsh -l netsim ${SERVER} "rm -rf ${NETSIM_XML_TEMPLATE_DIR}/* > /dev/null 2>&1"
        #ROPS=`getRopIntervals`
        #for ROP in $ROPS ; do
            #/usr/bin/rsh -l root ${SERVER} "if [ ! -d "${NETSIM_XML_TEMPLATE_DIR}/${ROP}" ] ; then mkdir -p "${NETSIM_XML_TEMPLATE_DIR}/${ROP}" ; chown -R netsim:netsim "${NETSIM_XML_TEMPLATE_DIR}/${ROP}"; fi"
        #done
    fi

    echo ${LIST} | egrep 'TCU02|SIU02|ERS' > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log "INFO: Transport sims found."
        log "INFO: Sending bcp_templates."
        /bin/cp -r ${GENSTATS_BCP_TEMPLATE_DIR} ${NETSIM_PMS_DIR}
    fi

    log "INFO: Deleting old sandbox_templates directory and creating new one"
    #/usr/bin/rsh -l netsim ${SERVER} "rm -rf ${NETSIM_SANDBOX_TEMPLATE_DIR} > /dev/null 2>&1"
    `rm -rf ${NETSIM_SANDBOX_TEMPLATE_DIR} > /dev/null 2>&1`
    #/usr/bin/rsh -l netsim ${SERVER} "mkdir -p ${NETSIM_SANDBOX_TEMPLATE_DIR}"
    `mkdir -p ${NETSIM_SANDBOX_TEMPLATE_DIR}`

    log "INFO: Sending sandbox templates."
    if [[ "${TYPE}" != "NSS"  &&  "${TYPE}" != "DO" ]]; then
        /bin/cp -r ${GENSTATS_SANDBOX_NRM3_TEMPLATE_DIR}/* ${NETSIM_SANDBOX_TEMPLATE_DIR}
    else
        /bin/cp -r ${GENSTATS_SANDBOX_TEMPLATE_DIR}/* ${NETSIM_SANDBOX_TEMPLATE_DIR}
    fi

    if [[ ${HAS_SCEF} -eq 1 ]]; then
        log "SCEF sims found : unzipping SCEF zip files"
        unzip -o ${NETSIM_SANDBOX_TEMPLATE_DIR}/SCEF.zip -d ${NETSIM_SANDBOX_TEMPLATE_DIR} > /dev/null 2>&1
        log "SCEF files unzipping completed"
    fi								

    #delete sandbox templates in /pms_tmpfs/xml_step/ location
    if [[ -d ${TMPFS_SANDBOX_DIR} ]];then
        log "INFO : Deleting sandbox templates in /pms_tmpfs"
        rm -rf ${TMPFS_SANDBOX_DIR}
    fi
    for PLAYBACK_NODE in ${TMPFS_PLAYBACKER_NODES};do
        echo ${PLAYBACK_SIM_LIST} | grep -s ${PLAYBACK_NODE} > /dev/null 2>&1
        if [[ $? -eq 0 ]];then
            PLAYBACK_NODE=${PLAYBACK_NODE/-/_}
            echo "INFO : Copying playback template file in tmpfs for ${PLAYBACK_NODE}"
            mkdir -p ${TMPFS_SANDBOX_DIR}/${PLAYBACK_NODE}/
            PLAYBACK_TEMPLATE_INPUT_LOC=${PLAYBACK_NODE}_STATS_INPUT_LOCATION
            cp -r ${!PLAYBACK_TEMPLATE_INPUT_LOC}/* ${TMPFS_SANDBOX_DIR}/${PLAYBACK_NODE}/
        fi
    done

    # Copy EPG template to pms_tmpfs partition to serve NRM3 and NRM4 15MB requirement through hardlink
    if [[ "${TYPE}" != "NSS" ]] && [[ "${TYPE}" != "NRM1.2" ]]; then
        echo ${LIST} | egrep 'EPG' > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            /bin/cp -r ${GENSTATS_EPG_TEMPLATE_DIR} ${GENSTATS_EPG_XML_STEP_DIR}
        fi
    fi

    # Remove any step files to make sure we start using the new templates
    #/usr/bin/rsh -l netsim ${SERVER} 'rm -f /pms_tmpfs/xml_step/*/*_step.*'
    `rm -f /pms_tmpfs/xml_step/*/*_step.*`
    #Deleting pms_tmpfs/xml_step/xml_templates 
    if [[ -d ${TMPFS_XML_TEMPLATES_DIR} ]];then
        log "INFO : Deleting xml templates in /pms_tmpfs"
        rm -rf ${TMPFS_XML_TEMPLATES_DIR}
    fi

done
