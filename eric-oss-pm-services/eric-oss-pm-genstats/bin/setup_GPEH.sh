#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2019
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 19.04
# Purpose       :  Script to do required setup (templates copy, cron etntries etc) for GPEH file generation
# Jira No       :  NSS-23422
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4755285/
# Description   :  NSS-MT fails with Latest Genstats ISO 19.04.2 - GPEH set up Fails.
# Date          :  04/02/2019
# Last Modified :  kumar.dhiraj7@tcs.com
####################################################

ROOT_DIR=`dirname $0`
. ${ROOT_DIR}/functions

SIM_DATA_FILE="/netsim/genstats/tmp/sim_data.txt"
GENSTATS_CONSOLELOGS="/netsim/genstats/logs/rollout_console/genstats_setup_GPEH.log"

expandRncIds() {
    local INPUT_STR=$1
    local INPUT_LIST=$(echo ${INPUT_STR} | sed 's/,/ /g')
    OUTPUT_LIST=""
    for ENTRY in ${INPUT_LIST} ; do
    local NUM_PARTS=$(echo ${ENTRY} | awk -F\- '{print NF}')
    if [ ${NUM_PARTS} -eq 2 ] ; then
        local INDEX=$(echo ${ENTRY} | awk -F\- '{print $1}')
        local END=$(echo ${ENTRY} | awk -F\- '{print $2}')
        while [ ${INDEX} -le ${END} ] ; do
        OUTPUT_LIST="${OUTPUT_LIST} ${INDEX}"
        let INDEX=${INDEX}+1
        done
    else
        OUTPUT_LIST="${OUTPUT_LIST} ${ENTRY}"
    fi
    done

    echo "${OUTPUT_LIST}"
}
cpFile()
{
    SRC=$1
    DEST=$2

    if [ ! -r ${SRC} ] ; then
    log "ERROR: File not found ${SRC}"
    exit 1
    fi

    SRC_FILE=`basename ${SRC}`
    log "   ${SRC_FILE}" >> $GENSTATS_CONSOLELOGS

    cp ${SRC} ${DEST}
    if [ $? -ne 0 ] ; then
    log "ERROR: cp failed for GPEH files"
    exit 1
    fi
}


getRbsGpehSimListForServer(){

    SERVER=$1
    MATCHED_RNC_LIST=""
    SIM_ON_SERVER_LIST=$(getSimListForServer ${SERVER})
    for SIM in ${RBS_GPEH_SIM_LIST} ; do
        echo "${SIM_ON_SERVER_LIST}" | grep -w ${SIM} > /dev/null
        if [ $? -eq 0 ] ; then
            cat "${SIM_DATA_FILE}" | grep ${SIM} | grep -w "PRBS" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                continue
            fi
            MATCHED_RNC_LIST="${MATCHED_RNC_LIST} ${SIM}"
        fi
    done

    echo "${MATCHED_RNC_LIST}"
}



copyTemplateParts() {
    log "Copying RNC GPEH templates parts"

    ROP_PERIOD_LIST=""
    RNC_PERIOD_LIST=""

    for WORKLOAD in ${GPEH_WORKLOAD_LIST} ; do
        ROP_PERIOD=$(echo ${WORKLOAD} | awk -F: '{print $1}')
        RNC_ID_LIST=$(echo ${WORKLOAD} | awk -F: '{print $6}')

        echo "${ROP_PERIOD_LIST}" | grep -w ${ROP_PERIOD} > /dev/null
        if [ $? -ne 0 ] ; then
            ROP_PERIOD_LIST="${ROP_PERIOD_LIST} ${ROP_PERIOD}"
        fi

        RNC_ID_LIST=$(expandRncIds "${RNC_ID_LIST}")
        for RNC_ID in ${RNC_ID_LIST} ; do
            RNC=$(printf "RNC%02d" ${RNC_ID})

            echo "${RNC_PERIOD_LIST}" | grep -w "${RNC}=${ROP_PERIOD}" > /dev/null
            if [ $? -ne 0 ] ; then
            RNC_PERIOD_LIST="${RNC_PERIOD_LIST} ${RNC}=${ROP_PERIOD}"
            fi
        done

    done

    for SERVER in $SERVERS ; do
        log " ${SERVER}" >> $GENSTATS_CONSOLELOGS
        if [ ${DEL_TEMPLATE_DIR} -eq 1 ] ; then
            log " Deleting all existing RNC GPEH templates on ${SERVER}"
            `rm -rf ${NETSIM_GPEH_TEMPLATE_DIR}`
        fi

        `if [ ! -d ${NETSIM_GPEH_TEMPLATE_DIR} ] ; then mkdir ${NETSIM_GPEH_TEMPLATE_DIR} ; fi`

            # Clear out tmp merge dir
        `rm -rf /tmp/merge`

        `rm -rf /netsim_users/gpeh_template_parts ; mkdir /netsim_users/gpeh_template_parts`
        RNC_LIST=`getSimListForServer ${SERVER}`

        for ROP_PERIOD in ${ROP_PERIOD_LIST} ; do
            log "  ${ROP_PERIOD}min" >> $GENSTATS_CONSOLELOGS

            `mkdir /netsim_users/gpeh_template_parts/${ROP_PERIOD}`

            #ignoring templates other than EBSW for ENM
            if [ ${ENV_TYPE} -eq 0 ] ; then
                cpFile ${GPEH_TEMPLATE_DIR}/Other_templates.tar.gz  /netsim_users/gpeh_template_parts/${ROP_PERIOD}

            for RNC in ${RNC_LIST} ; do
                echo "${RNC_PERIOD_LIST}" | grep -w "${RNC}=${ROP_PERIOD}" > /dev/null
                if [ $? -eq 0 ] ; then
                    # EBSW Load input is the same for both 1/15min
                    cpFile ${GPEH_TEMPLATE_DIR}/${RNC}.ebsw_templates.tar.gz  /netsim_users/gpeh_template_parts/${ROP_PERIOD}
                    cpFile ${GPEH_TEMPLATE_DIR}/${ROP_PERIOD}/${RNC}.wncs_templates.tar.gz  /netsim_users/gpeh_template_parts/${ROP_PERIOD}
                    cpFile ${GPEH_TEMPLATE_DIR}/${ROP_PERIOD}/${RNC}.wgeo_templates.tar.gz  /netsim_users/gpeh_template_parts/${ROP_PERIOD}
                fi
            done

            else
                cpFile ${GPEH_TEMPLATE_DIR}/"RNC".ebsw_templates.tar.gz  /netsim_users/gpeh_template_parts/${ROP_PERIOD}
            fi

        done

        # RBS GPEH Support
        # Copy the RBS GPEH template file which is required to create GPEH sub file to Netsim server

        SIM_LIST=`getRbsGpehSimListForServer ${SERVER}`

        if [ ! -z "${SIM_LIST}" ] ; then
            cpFile ${GPEH_TEMPLATE_DIR}/rbs_gpeh.bin.gz  ${NETSIM_GPEH_TEMPLATE_DIR}
        fi
    done
}

makeTemplates() {
    log "Create GPEH templates"

    for WORKLOAD in ${GPEH_WORKLOAD_LIST} ; do
    ROP_PERIOD=$(echo ${WORKLOAD} | awk -F: '{print $1}')
    WORKLOAD_NAME=$(echo ${WORKLOAD} | awk -F: '{print $2}')
    TOTAL_SIZE=$(echo ${WORKLOAD} | awk -F: '{print $3}')
    EBSW_SIZE=$(echo ${WORKLOAD} | awk -F: '{print $4}')
    RNC_ID_LIST=$(echo ${WORKLOAD} | awk -F: '{print $6}')

    RNC_IN_WORKLOAD_LIST=""
    RNC_ID_LIST=$(expandRncIds "${RNC_ID_LIST}")
    for RNC_ID in ${RNC_ID_LIST} ; do
        RNC=$(printf "RNC%02d" ${RNC_ID})
        RNC_IN_WORKLOAD_LIST="${RNC_IN_WORKLOAD_LIST} ${RNC}"
    done

    DEST_DIR=${NETSIM_GPEH_TEMPLATE_DIR}/${ROP_PERIOD}_${WORKLOAD_NAME}

    MAKE_GPEH_TEMPLATES_CMD="${NETSIM_BIN_DIR}/makeGPEHtemplates -i /netsim_users/gpeh_template_parts/${ROP_PERIOD} -o ${DEST_DIR} -t ${TOTAL_SIZE} -v ${ENV_TYPE} -e ${EBSW_SIZE}"
    if [ ${SKIP_IF_EXISTS} -eq 1 ] ; then
        MAKE_GPEH_TEMPLATES_CMD="${MAKE_GPEH_TEMPLATES_CMD} -s"
    fi

    log " Creating GPEH for ${WORKLOAD_NAME} ${ROP_PERIOD}min workload , total size = $TOTAL_SIZE, EBSW Size = $EBSW_SIZE ENV_TYPE = $ENV_TYPE" >> $GENSTATS_CONSOLELOGS
    log "  ${MAKE_GPEH_TEMPLATES_CMD}" >> $GENSTATS_CONSOLELOGS
    for SERVER in $SERVERS ; do
        log "  ${SERVER}" >> $GENSTATS_CONSOLELOGS
        if [ ${SKIP_IF_EXISTS} -eq 0 ] ; then
        if [ ${ENV_TYPE} -eq 0 ] ; then
            `if [ -d ${DEST_DIR} ] ; then rm -rf ${DEST_DIR} ; fi`
        fi
        fi
        `if [ ! -d ${DEST_DIR} ] ; then mkdir ${DEST_DIR} ; fi`

        # Need to work out if what(if any) RNCs on this server are part of this workload
        RNC_ON_SERVER_LIST=$(getSimListForServer ${SERVER})
        MATCHED_RNC_LIST=""
        for RNC_ON_SERVER in ${RNC_ON_SERVER_LIST} ; do
        echo "${RNC_IN_WORKLOAD_LIST}" | grep -w ${RNC_ON_SERVER} > /dev/null
        if [ $? -eq 0 ] ; then
            MATCHED_RNC_LIST="${MATCHED_RNC_LIST} ${RNC_ON_SERVER}"
        fi
        done
        if [ -z "${MATCHED_RNC_LIST}" ] ; then
        log "    No matching RNCs for this Workload" >> $GENSTATS_CONSOLELOGS
        else
        log "   ${MATCHED_RNC_LIST}" >> $GENSTATS_CONSOLELOGS
        DATE=$(date "+%Y%m%d%H%M%S")
        LOG=${NETSIM_LOG_DIR}/makeGpehTemplates.${ROP_PERIOD}_${WORKLOAD_NAME}_${DATE}.log
        `${MAKE_GPEH_TEMPLATES_CMD} -r "${MATCHED_RNC_LIST}" >  ${LOG} 2>&1`
        `tail --lines=100 ${LOG} | egrep 'ERROR|illegal' > /dev/null`
        if [ $? -eq 0 ] ; then
            log "ERROR: ${CMD} failed"
            `tail --lines=100 ${LOG}`
                 exit 1
        fi
        fi
        #rcpFile ${GPEH_TEMPLATE_DIR}/P5_RBS_276K.gpeh netsim@${SERVER}:${DEST_DIR}/rbs_gpeh_sub.bin
    done
    wait
    done
}

moveTemplates(){
        log "INFO: Moving generated templates from ${NETSIM_PMS_DIR} to ${LINK_GPEH_TEMPLATE_DIR} "
    for SERVER in $SERVERS ; do
        log "  ${SERVER}" >> $GENSTATS_CONSOLELOGS
        `if [ -d ${NETSIM_GPEH_TEMPLATE_DIR} ] ; then rm -rf ${NETSIM_GPEH_TEMPLATE_DIR} ; fi`
        `if [ ! -d ${LINK_GPEH_TEMPLATE_DIR} ] ; then mkdir -p ${LINK_GPEH_TEMPLATE_DIR} ; fi`
        `rm -f ${NETSIM_PMS_DIR}/gpeh_templates/*/*.bin`
        `cp -rf ${NETSIM_PMS_DIR}/gpeh_templates ${LINK_GPEH_TEMPLATE_DIR}/`
    done
}

updateCrontab() {

    log "Updating crontab"
    for SERVER in $SERVERS ; do
            log " $SERVER" >> $GENSTATS_CONSOLELOGS

            `crontab -l | egrep -v '^# |genGPEH|genRbsGpeh' > /tmp/rec_new_crontab`

            for WORKLOAD in ${GPEH_WORKLOAD_LIST} ; do
                    ROP_PERIOD=$(echo ${WORKLOAD} | awk -F: '{print $1}')
                    WORKLOAD_NAME=$(echo ${WORKLOAD} | awk -F: '{print $2}')
                    ACTIVE_HOURS=$(echo ${WORKLOAD} | awk -F: '{print $5}')
                    RNC_ID_LIST=$(echo ${WORKLOAD} | awk -F: '{print $6}')

                    if [ ${ROP_PERIOD} -eq 15 ] ; then
                    MINUTE_FIELD="0,15,30,45"
                    elif [ ${ROP_PERIOD} -eq 1 ] ; then
                    MINUTE_FIELD="*"
                    else
                    echo "ERROR: Invalid value for ROP_PERIOD ${ROP_PERIOD}"
                    exit 1
                    fi

                    RNC_IN_WORKLOAD_LIST=""
                    RNC_ID_LIST=$(expandRncIds "${RNC_ID_LIST}")
                    for RNC_ID in ${RNC_ID_LIST} ; do
                    RNC=$(printf "RNC%02d" ${RNC_ID})
                    cat "${SIM_DATA_FILE}" | grep ${RNC} | grep -w "PRBS" > /dev/null 2>&1
                    if [ $? -eq 0 ]; then
                        continue
                    fi
                    RNC_IN_WORKLOAD_LIST="${RNC_IN_WORKLOAD_LIST} ${RNC}"
                    done

                    # Need to work out if what(if any) RNCs on this server are part of this workload
                    RNC_ON_SERVER_LIST=$(getSimListForServer ${SERVER})
                    MATCHED_RNC_LIST=""
                    for RNC_ON_SERVER in ${RNC_ON_SERVER_LIST} ; do
                    echo "${RNC_IN_WORKLOAD_LIST}" | grep -w ${RNC_ON_SERVER} > /dev/null
                    if [ $? -eq 0 ] ; then
                        MATCHED_RNC_LIST="${MATCHED_RNC_LIST} ${RNC_ON_SERVER}"
                    fi
                    done
                    if [ -z "${MATCHED_RNC_LIST}" ] ; then
                    log "    ${ROP_PERIOD}min ${WORKLOAD_NAME} workload: No matching RNCs" >> $GENSTATS_CONSOLELOGS
                    else
                    MATCHED_RNC_LIST=$(echo "${MATCHED_RNC_LIST}" | sed 's/^ //')
                    log "    ${ROP_PERIOD}min ${WORKLOAD_NAME} workload: ${MATCHED_RNC_LIST}" >> $GENSTATS_CONSOLELOGS

                    CMD="${MINUTE_FIELD} ${ACTIVE_HOURS} * * * ${NETSIM_BIN_DIR}/genGPEH -t ${NETSIM_GPEH_TEMPLATE_DIR}/${ROP_PERIOD}_${WORKLOAD_NAME} -r ${ROP_PERIOD} -v ${ENV_TYPE} -l \"${MATCHED_RNC_LIST}\""
                    echo "${CMD} >> ${NETSIM_LOG_DIR}/genGPEH_${ROP_PERIOD}min.log 2>&1" >> /tmp/rec_new_crontab
                    fi
            done
            # RBS GPEH Support
            SIM_LIST=`getRbsGpehSimListForServer ${SERVER}`

            if [ ! -z "${SIM_LIST}" ] ; then

                SIM_LIST=$(echo "${SIM_LIST}" | sed 's/^ //')

                for ROP_PERIOD in ${GPEH_RBS_WORKLOAD};do

                    log "    ${ROP_PERIOD} min RBS GPEH workload: ${MATCHED_SIMLIST}" >> $GENSTATS_CONSOLELOGS

                    MINUTE_FIELD="*"
                    if [ ${ROP_PERIOD} -eq 1 ] ; then
                        MINUTE_FIELD="*"
                    elif [ ${ROP_PERIOD} -eq 15 ];then
                        MINUTE_FIELD="0,15,30,45"
                    else
                        echo "ERROR: Invalid value for ROP_PERIOD ${ROP_PERIOD}"
                        exit 1
                    fi

                    CMD="${MINUTE_FIELD} 0-23 * * * ${NETSIM_BIN_DIR}/genRbsGpeh -r ${ROP_PERIOD} -v ${ENV_TYPE} -l \"${SIM_LIST}\""
                    echo "${CMD} >> ${NETSIM_LOG_DIR}/genRbsGpeh_${ROP_PERIOD}min.log 2>&1" >> /tmp/rec_new_crontab
                done

            fi

            `crontab /tmp/rec_new_crontab`
    done
}

SKIP_IF_EXISTS=0
TEMPLATE_ONLY=0
CONFIGFILE=/netsim/netsim_cfg
DEL_TEMPLATE_DIR=0
#Specifies its either ENM or OSSRC. 0 => OSSRC, 1 => ENM
ENV_TYPE=0
while getopts  "s:c:t:k:d:r:v:" flag
do
    case "$flag" in

    c) CONFIGFILE="$OPTARG";;
    s) SERVER_LIST="$OPTARG";;
    t) TEMPLATE_ONLY=1;;
    k) SKIP_IF_EXISTS=1;;
    d) TEMPLATE_DIR="$OPTARG";;
    r) DEL_TEMPLATE_DIR=1;;
    v) ENV_TYPE="$OPTARG";;

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

if [ -z "${GPEH_WORKLOAD_LIST}" ] ; then
    echo "ERROR: GPEH_WORKLOAD_LIST not defined"
    exit 1
fi
for WORKLOAD in ${GPEH_WORKLOAD_LIST} ; do
    NUM_FIELDS=`echo ${WORKLOAD} | awk -F: '{print NF}'`
    if [ ${NUM_FIELDS} -ne 6 ] ; then
    echo "ERROR: Incorrect format for GPEH_WORKLOAD_LIST ${WORKLOAD}"
    echo "Format <RopPeroid>:<name>:<total size>:<ebsw size>:<hours>:<rnc id list> ..."
    exit 1
    fi
done

checkPMDIR
if [ $? -ne 0 ] ; then
    log "ERROR: PMDIR not set correctly"
    exit 1
else
    GPEH_TEMPLATE_DIR=${PMDIR}/gpeh_templates
fi

if [ ! -z "${TEMPLATE_DIR}" ] ; then
    echo "INFO: Overridding ${GPEH_TEMPLATE_DIR} with ${TEMPLATE_DIR}"
    GPEH_TEMPLATE_DIR=${TEMPLATE_DIR}
fi

NETSIM_PMS_DIR=/netsim_users/pms
NETSIM_BIN_DIR=${NETSIM_PMS_DIR}/bin
NETSIM_LOG_DIR=${NETSIM_PMS_DIR}/logs
NETSIM_GPEH_TEMPLATE_DIR=${NETSIM_PMS_DIR}/gpeh_templates

if [ ! -d ${GPEH_TEMPLATE_DIR} ] ; then
    echo "ERROR: GPEH Template dir not found: ${GPEH_TEMPLATE_DIR}"
    exit 1
fi

#Get the Simulation list for which RBS GPEH generation is needed
#RBS_GPEH_WORKLOAD_LIST="<SIM Name>:<RBS RANGE>[,<RBS RANGE>]"
#RBS_GPEH_WORKLOAD_LIST="RNC04:10-12,15,20-50"
RBS_GPEH_SIM_LIST=""
for RBS_GPEH_WORKLOAD in $RBS_GPEH_WORKLOAD_LIST; do
    SIM_NAME=`echo ${RBS_GPEH_WORKLOAD} | awk -F: '{print $1}'`
    RBS_GPEH_SIM_LIST="${RBS_GPEH_SIM_LIST} ${SIM_NAME}"
done


copyTemplateParts
makeTemplates

#changes to produce hard link
if [ ${ENV_TYPE} -eq 1 ] ; then
    log "INFO: Changes being done to generate hard link at the output for GPEH"
    LINK_GPEH_TEMPLATE_DIR=/pms_tmpfs/xml_step
    NETSIM_GPEH_TEMPLATE_DIR=${LINK_GPEH_TEMPLATE_DIR}/gpeh_templates
    moveTemplates
fi

if [ ${TEMPLATE_ONLY} -eq 0 ] ; then
    updateCrontab
fi

log "Deleting temp files"
for SERVER in $SERVERS ; do
    log " $SERVER" >> $GENSTATS_CONSOLELOGS
    `rm -rf /netsim_users/gpeh_template_parts`
    `rm -rf /tmp/merge`
done
