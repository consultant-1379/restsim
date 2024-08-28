#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2020
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 22.06
# Purpose       :  The purpose of this script to setup the required configurations for GenStats
# Jira No       :  NSS-35517
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/11675757/
# Description   :  Adding 20mb file support for SCEF in MD_1
# Date          :  29/01/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################


BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

GENSTATS_CONSOLELOGS="/netsim/genstats/logs/rollout_console/genstats_pm_setup_stats_recordings.log"
TMPFS_SANDBOX_DIR="/pms_tmpfs/xml_step/sandbox_templates/"
MD_1_NODE_TEMPLATE_LIST="mtas_md_1 sgsn_md_1"
CONFIGFILE=/netsim/netsim_cfg
CREATE_SCANNERS=1
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
NETSIM_SANDBOX_DIR=${NETSIM_PMS_DIR}/sandbox_templates
NETSIM_TEMPLATES_DIR=${NETSIM_PMS_DIR}/xml_templates
NETSIM_GENSTATS_DIR=/netsim/genstats

HAS_WRAN=0
HAS_LTE=0
HAS_MSC=0
HAS_SMSF=0

for SERVER in $SERVERS ; do
    SERVER_SIM_LIST=`getSimListForServer ${SERVER}`
    for SERVER_SIM in ${SERVER_SIM_LIST} ; do
        SIM_TYPE=`getSimType ${SERVER_SIM}`
        if [ "${SIM_TYPE}" = "WRAN" ] ; then
            HAS_WRAN=1
        elif [ "${SIM_TYPE}" = "LTE" ] ; then
            HAS_LTE=1
        elif [ "${SIM_TYPE}" = "SMSF" ] ;then
            HAS_SMSF=1
        elif [[ "${SIM_TYPE}" = "vMSC-HC" ]] || [[ "${SIM_TYPE}" = "vMSC" ]] || [[ "${SIM_TYPE}" = "MSCv" ]] || [[ "${SIM_TYPE}" = "MSC-vIP-STP" ]] || [[ "${SIM_TYPE}" = "MSC-IP-STP" ]] || [[ "${SIM_TYPE}" = "CTC-MSC-BC-BSP" ]] || [[ "${SIM_TYPE}" = "MSC-DB-BSP" ]] || [[ "${SIM_TYPE}" = "MSC-DB" ]] || [[ "${SIM_TYPE}" = "MSC-BC-IS" ]] || [[ "${SIM_TYPE}" = "MSC-BC-BSP" ]]; then
            HAS_MSC=1
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
        echo shroot | su root -c "rm -rf  /tmp/netypes.txt; rm -rf /tmp/showstartednodes.txt; rm -rf /tmp/nodetypes.txt; rm -rf /tmp/nodetypes.tmp.txt; rm -rf /netsim_users/.count"

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
    if [[ $TYPE != "DO" ]] ;then
        log "INFO: Initiating Cell Trace Configuration finder script."
        python /netsim_users/auto_deploy/bin/celltraceConfigFinder.py
       
    else
        log "INFO: Cell Trace Configuration finder script NOT needed to be executed for ${SIM_TYPE} in ${TYPE}"
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

    hostname=`hostname`
    real_data_cnt=0
    firstDir="/"

    real_data_dir=$(find / -maxdepth 3 -type d 2>&1 | grep -v -i "Permission denied" | grep "HSTNTX01LT9" | head -1 | sed 's/ //g')

        if [[ ! -z ${real_data_dir} ]]; then
                real_data_cnt=$(ls ${real_data_dir} | wc -l)
        fi

        if [[ ${real_data_cnt} -gt 0 ]]; then
                firstDir="${firstDir}$(echo ${real_data_dir} | awk -F'/' '{print $2}')"
        else
                firstDir="/store"
                if [[ ! -d ${firstDir} ]]; then
                        #rsh -l root ${hostname} "mkdir ${firstDir}"
                        echo shroot | su root -c "mkdir ${firstDir}"
                fi
        fi

        #rsh -l root ${hostname} "chown -R netsim:netsim ${firstDir}"
        echo shroot | su root -c "chown -R netsim:netsim ${firstDir}"

        if [[ ! -d "${firstDir}/EBM_Sample_Templates" ]]; then
                mkdir "${firstDir}/EBM_Sample_Templates"
        fi

        if [[ ! -d "${firstDir}/EBM_HardLink" ]]; then
                mkdir "${firstDir}/EBM_HardLink"
        fi

        EBM_SAM_TEMP="${firstDir}/EBM_Sample_Templates/"


    MME_REF_CFG="/netsim_users/pms/etc/sgsn_mme_ebs_ref_fileset.cfg"
    if [[ -f ${MME_REF_CFG} ]]; then
        rm -f ${MME_REF_CFG}
    fi

    log "INFO: setup UETR_CTR"
    ${BIN_DIR}/pm_recordings_UETR_CTR.sh -s ${SERVER} -c ${CONFIGFILE}
    if [ $? -ne 0 ] ; then
        log "ERROR: pm_recordings_UETR_CTR failed"
        log "ERROR: pm_recordings_UETR_CTR failed" >> $GENSTATS_CONSOLELOGS
        exit 1
    fi

    for file in `ls /netsim_users/pms/rec_templates/ | grep "ebs"`; do
                cp /netsim_users/pms/rec_templates/${file} ${EBM_SAM_TEMP}
        done

        log "INFO: Creating cfg file for EBM data."
    python /netsim_users/auto_deploy/bin/CreateMmeRefCfg.py

    log "INFO: setup GPEH"
    if [[ "${TYPE}" != "NRM1.2" ]]; then
        ${BIN_DIR}/setup_GPEH.sh -s ${SERVER} -c ${CONFIGFILE} -v 1
        if [ $? -ne 0 ] ; then
            log "ERROR: setup_GPEH failed"
            log "ERROR: setup_GPEH failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi

    log "INFO: setting up PCC,PCG,UDM and SC simulations"
    cp ${NETSIM_GENSTATS_DIR}/xml_templates/15/PCC_PCG_node.template.gz ${NETSIM_TEMPLATES_DIR}/15/PCC_PCG_node.xml.gz
    PCC_XML_TEMPLATES=`ls ${NETSIM_TEMPLATES_DIR}`
    if [[ ${TYPE} != "DO" ]]; then
        PCC_XML_TEMPLATES=`ls ${NETSIM_TEMPLATES_DIR} | grep -vw 15`
    fi
    for folder in ${PCC_XML_TEMPLATES}; do
        cp ${NETSIM_GENSTATS_DIR}/xml_templates/1/PCC_PCG_node.template.gz ${NETSIM_TEMPLATES_DIR}/${folder}/PCC_PCG_node.xml.gz
    done
    cp ${NETSIM_GENSTATS_DIR}/xml_templates/1/UDM_SC_node.template.gz ${NETSIM_TEMPLATES_DIR}/1/UDM_SC_node.xml.gz
    cp ${NETSIM_GENSTATS_DIR}/xml_templates/15/UDM_SC_node.template.gz ${NETSIM_TEMPLATES_DIR}/15/UDM_SC_node.xml.gz
    cp ${NETSIM_GENSTATS_DIR}/xml_templates/15/SC_only_node.template.gz ${NETSIM_TEMPLATES_DIR}/15/SC_only_node.xml.gz
    # using PCC 0.5mb file for RDM
    mkdir  -p ${NETSIM_SANDBOX_DIR}/RDM/
    cp ${NETSIM_GENSTATS_DIR}/xml_templates/15/UDM_SC_node.template.gz ${NETSIM_SANDBOX_DIR}/RDM/UDM_SC_node.xml.gz

    if [[ ${HAS_SMSF} -eq 1 ]];then
        mkdir ${NETSIM_TEMPLATES_DIR}/5/
        cp ${NETSIM_GENSTATS_DIR}/xml_templates/1/UDM_SC_node.template.gz ${NETSIM_TEMPLATES_DIR}/5/UDM_SC_node.xml.gz
    fi
 
    if [[ "${TYPE}" == "MD_1" ]]; then
         MD_1_TEMPLATE_PATH="/pms_tmpfs/xml_step/xml_templates/15"
         for node_template in $MD_1_NODE_TEMPLATE_LIST
          do
            TEMPLATE=$TEMPLATE_PATH/$node_template
            cp ${NETSIM_GENSTATS_DIR}/xml_templates/15/$node_template $TEMPLATE_PATH/
        done
     fi

    #FOR MSC DATASETS PREPARATION
    if [[ ${HAS_MSC} -eq 1 ]] && [[ ${TYPE} != "NSS" ]]; then
      log "INFO: Preparing data sets for MSC stats"
      current_date=`date -u +'%Y%m%d'`
      end_date=`date -u +'%Y%m%d'`
      next_date=`date -u -d "+1 day" +'%Y%m%d'`
      start_min=0
      end_min=15

      mkdir -p ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/ ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/MSC_DB_BSP ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/MSC_BC
      for i in {1..96};do
           start_time_prefix=`date -u -d "00:00 ${start_min} min" +'%H%M'`
           end_time_prefix=`date -u -d "00:00 ${end_min} min" +'%H%M'`
           if [[ $i -eq 96 ]];then
               end_date=${next_date}
           fi
           cp ${NETSIM_SANDBOX_DIR}/MSC/MSC_BC/CSTART_DATE.START_TIME-END_DATE.END_TIME_NODE ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/MSC_BC/G${current_date}.${start_time_prefix}-${end_date}.${end_time_prefix}
           cp ${NETSIM_SANDBOX_DIR}/MSC/MSC_DB_BSP/CSTART_DATE.START_TIME-END_DATE.END_TIME_NODE ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/MSC_DB_BSP/C${current_date}.${start_time_prefix}-${end_date}.${end_time_prefix}
           cp ${NETSIM_SANDBOX_DIR}/MSC/CSTART_DATE.START_TIME-END_DATE.END_TIME_NODE ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates/C${current_date}.${start_time_prefix}-${end_date}.${end_time_prefix}
           start_min=`expr ${start_min} + 15`
           end_min=`expr ${end_min} + 15`
      done
      chmod -R 755 ${NETSIM_SANDBOX_DIR}/MSC/MSC_templates
   fi

    if [ ${CREATE_SCANNERS} -eq 1 ] ; then
        log "INFO: Create scanners"
        ${BIN_DIR}/scanners.sh -d -a create -s ${SERVER}
        if [ $? -ne 0 ] ; then
            log "ERROR: scanners.sh failed"
            log "ERROR: scanners.sh failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
    fi

    if [ ! "${SET_BANDWIDTH_LIMITING}" = "OFF" ] ; then
        log "INFO: Apply bandwidth limiting"
        #/usr/bin/rsh -l root ${SERVER} ${BIN_DIR}/limitbw -n -c > ${NETSIM_LOG_DIR}/limitbw.log
        echo shroot | su root -c "${BIN_DIR}/limitbw -n -c > ${NETSIM_LOG_DIR}/limitbw.log"

        #/usr/bin/rsh -l root ${SERVER} ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log
        echo shroot | su root -c "${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log"

        if [ $? -ne 0 ] ; then
            log "ERROR: limitbw failed"
            log "ERROR: limitbw failed" >> $GENSTATS_CONSOLELOGS
            exit 1
        fi
        #/usr/bin/rsh -l root ${SERVER} "crontab -l | grep -v limitbw > /tmp/new_crontab"
        echo shroot | su root -c "crontab -l | grep -v limitbw > /tmp/new_crontab"

        #/usr/bin/rsh -l root ${SERVER} "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"0 0 * * * ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"

        #/usr/bin/rsh -l root ${SERVER} "echo \"20 0 * * * ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"20 0 * * * ${BIN_DIR}/limitbw -n -g >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"

        #/usr/bin/rsh -l root ${SERVER} "echo \"@reboot ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"
        echo shroot | su root -c "echo \"@reboot ${BIN_DIR}/limitbw -n -c >> ${NETSIM_LOG_DIR}/limitbw.log 2>&1\" >> /tmp/new_crontab"

        #/usr/bin/rsh -l root ${SERVER} "crontab /tmp/new_crontab"
        echo shroot | su root -c "crontab /tmp/new_crontab"

    fi

    log "INFO: Timesync"
    ${BIN_DIR}/timesync -d -s ${SERVER}

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
            echo "" >> /netsim/netsim_cfg

            #/usr/bin/rsh -l netsim ${SERVER} "echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /netsim/netsim_cfg"
            echo "PERIODIC_HC_INTERVAL=\"15M\"" >> /netsim/netsim_cfg
        fi
        if [[ ${phc_check_second} -eq 0 ]]; then
            #/usr/bin/rsh -l netsim ${SERVER} "echo '' >> /tmp/${SERVER}"
            echo "" >> /tmp/${SERVER}

            #/usr/bin/rsh -l netsim ${SERVER} "echo 'PERIODIC_HC_INTERVAL=\"15M\"' >> /tmp/${SERVER}"
            echo "PERIODIC_HC_INTERVAL=\"15M\"" >> /tmp/${SERVER}
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

