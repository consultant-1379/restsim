#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2016
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

ROOT_DIR=`dirname $0`
. ${ROOT_DIR}/functions


copyTemplate() {

log "Downloading templates for version $RECORDING_FILE_VERSION"

curl -L "https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/service/local/repositories/nss/content/com/ericsson/nss/Genstats/recording_files/$recording_file_version/recording_files-$recording_file_version.zip" -o $TEMP_DIR/recording_files.zip



unzip -o ${TEMP_DIR}/recording_files.zip -d $TEMP_DIR >> ${LOG} 2>&1
if [ $? -ne 0 ] ; then
echo "Error : While infating $TEMP_DIR/recording_files.zip"
fi

mv $TEMP_DIR/gpeh_templates ${GENSTAT_DIR}
if [ ! -d ${GPEH_TEMPLATE_DIR} ] ; then
log "ERROR : to move gpeh_tempaltes to ${GENSTAT_DIR}"
fi
 
}


updateNetsimCfg() {
cat <<EOT >> ${CONFIGFILE}
########### GPEH CONFIGURATION ############

V_5_3878_RNC_P_VER=w13a

V_4_3202_RNC_P_VER=w13a

V_2_2693_RNC_P_VER=w13a
V_6_940_RNC_P_VER=w13a
V_7_1202_RNC_P_VER=w13a

V_7_1202_RNC_FMT_VER=" 7- 2"
V_6_940_RNC_FMT_VER=" 7- 2"
V_8_1349_RNC_FMT_VER=" 7- 2"
V_7_1543_RNC_FMT_VER=" 7- 2"
V_7_1659_RNC_FMT_VER=" 7- 2"
V_6_702_RNC_FMT_VER=" 7- 2"

V_3_3141_RNC_FMT_VER=" 7- 2"

V_5_3878_RNC_FMT_VER=" 7- 2"

GPEH_CELLS_PER_MP=20
GPEH_CELLS_PER_MP_CONFIG_LIST="01:20:10"
GPEH_MP_CONFIG_LIST="01:15:33,1 16:20:39,1"

GPEH_WORKLOAD_LIST="15:default:20269794:28035588:0-23:01-05 15:default:20269794:58315929:0-23:06-15 15:default:20269794:86016000:0-23:16-20"

RBS_GPEH_WORKLOAD_LIST="RNC01:1:33 RNC02:1:33 RNC03:1:33 RNC04:1:33 RNC05:1:33 RNC06:1:33 RNC07:1:33 RNC08:1:33 RNC09:1:33 RNC10:1:33 RNC11:1:33 RNC12:1:33 RNC13:1:33 RNC14:1:33 RNC15:1:33 RNC16:1:33 RNC17:1:33 RNC18:1:33 RNC19:1:33 RNC20:1:33"
EOT

}

CONFIGFILE=/netsim/netsim_cfg
#Specifies its either ENM or OSSRC. 0 => OSSRC, 1 => ENM
ENV_TYPE=1
recording_file_version=17.8.2
while getopts  "c:rfp:v:" flag
do
    case "$flag" in

    c) CONFIGFILE="$OPTARG";;
    v) ENV_TYPE="$OPTARG";;
    rfv)recording_file_version="$OPTARG";;
    *) printf "Usage: %s < -c configfile > <-s serverlist>\n" $0
           exit 1;;   esac
done



if [ ! -r ${CONFIGFILE} ] ; then
    echo "ERROR: Cannot find ${CONFIGFILE}"
    exit 1
fi


. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

DATE=$(date "+%Y%m%d%H%M%S")
NETSIM_PMS_DIR=/netsim_users/pms
GENSTAT_DIR=/netsim/genstats/
GPEH_TEMPLATE_DIR=${GENSTAT_DIR}/gpeh_templates
NETSIM_LOG_DIR=${NETSIM_PMS_DIR}/logs
LOG=${NETSIM_LOG_DIR}/setup_genstat_gpeh_${DATE}.log
NETSIM_PMS_DIR=/netsim_users/pms
NETSIM_GPEH_TEMPLATE_DIR=${NETSIM_PMS_DIR}/gpeh_templates

#TEMP_DIR="/netsim_users/gpeh_install"
SERVER=`hostname`

log "Log file: ${LOG}"
log " Deleting all existing RNC GPEH templates on ${SERVER}" > ${LOG}

if [ -d ${NETSIM_GPEH_TEMPLATE_DIR} ] ; then
rm -rf ${NETSIM_GPEH_TEMPLATE_DIR}
fi


if [ ! -d ${GENSTAT_DIR} ] ; then
mkdir -p ${GENSTAT_DIR}
fi

#mkdir -p ${TEMP_DIR}

#copyTemplate
updateNetsimCfg
log "Updation of ${CONFIGFILE} is done" >> ${LOG}

#log "Deleting temp files"
#rm -rf ${TEMP_DIR}


log "INFO: setup GPEH"
    /netsim_users/pms/bin/setup_GPEH.sh -s ${SERVER} -c ${CONFIGFILE} -v 1
    if [ $? -ne 0 ] ; then
        log "ERROR: setup_GPEH failed"
        exit 1
    fi

log "setup_genstat_GPEH.sh ended"
