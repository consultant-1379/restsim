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
# Version no    :  NSS 18.3
# Purpose       :  Script is responsible for checking pre-condition of server before running periodic HC
# Jira No       :  NSS-16209
# Gerrit Link   :
# Description   :  Checking for duplicate sims and sims with verison id(LTE and RNC)
# Date          :  18/12/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

FUNC_FILE="/netsim_users/pms/bin/functions"

if [[ -f "${FUNC_FILE}" ]]; then
    . ${FUNC_FILE}
else
    echo "ERROR: ${FUNC_FILE} file not found."
    exit 1
fi

PMS_PATH="/pms_tmpfs/"
NETSIM_DIR="/netsim/netsimdir/"
NETSIM_DBDIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir/"

UNSUPPORTED_SIMS="CORE-MGW-15B-16A-UPGIND-V1 CORE-SGSN-42A-UPGIND-V1 PRBS-99Z-16APICONODE-UPGIND-MSRBSV1-LTE99 RNC-15B-16B-UPGIND-V1 LTEZ9334-G-UPGIND-V1-LTE95 LTEZ8334-G-UPGIND-V1-LTE96 LTEZ7301-G-UPGIND-V1-LTE97 RNCV6894X1-FT-RBSU4110X1-RNC99 LTE17A-V2X2-UPGIND-DG2-LTE98 LTE16A-V8X2-UPGIND-PICO-FDD-LTE98 RNC-FT-UPGIND-PRBS61AX1-RNC01 GSM-FT-BSC_17-Q4_V4X2 GSM-ST-BSC-16B-APG43L-X5 RNC-FT-UPGIND-PRBS61AX1-RNC31 RNCV10305X2-FT-RBSUPGIND"

UNSUPPORTED_NES="VNFM VSD NFVO OPENMANO CISCO JUNIPER"

validateSims(){

    re="^[0-9]+$"

    dbdir_sims=$(ls -ld ${NETSIM_DBDIR}*/ | cut -d'/' -f7 | sort -u)

    dir_sims=""

    for sim_name in ${dbdir_sims}; do

        for nes in ${UNSUPPORTED_NES}; do
            echo ${sim_name} | grep ${nes} > /dev/null
            if [[ $? -eq 0 ]]; then
                continue
            fi
        done

        echo ${UNSUPPORTED_SIMS} | grep -w ${sim_name} > /dev/null

        if [[ $? -eq 0 ]]; then
            continue
        fi

        value=""
        versionId="false"
        
        echo ${sim_name} | grep "-" > /dev/null
        
        if [[ $? -eq 0 ]]; then
            value=$(echo ${sim_name} | rev | cut -d'-' -f1 | rev | grep "\.")
            if [[ ! -z ${value} ]]; then
                value=$(echo ${value} | sed 's/\.//g')
                if [[ ${value} =~ $re ]]; then
                    versionId="true"
                    log "ERROR: Simulation ${sim_name} found in ${NETSIM_DIR} with version ID in it's name. Please remove this simulation."
                fi
            fi
        fi
        
        if [[ ${sim_name} = *"LTE"* ]] || [[ ${sim_name} = *"RNC"* ]]; then
            if [[ ${versionId} = "true" ]]; then
                value=$(echo ${sim_name} | rev | cut -d'-' -f2 | rev)
            else
                value=$(echo ${sim_name} | rev | cut -d'-' -f1 | rev)
            fi
            
            if [[ ! -z ${value} ]]; then
                checkDuplicacy "${value}" "false"
            else
                log "ERROR: Incorrect simulation name ${sim_name}."
            fi
        else
            if [[ ${versionId} = "true" ]]; then
                value=$(echo ${sim_name} | rev | cut -d'-' -f2- | rev)
            else
                value=$(echo ${sim_name})
            fi
            
            if [[ ! -z ${value} ]]; then
                checkDuplicacy "${value}" "true"
            else
                log "ERROR: Incorrect simulation name ${sim_name}."
            fi
        fi
        
    done
}

checkDuplicacy(){

    val=$1
    nonLteRNC=$2
    
    if [[ ${nonLteRNC} = "true" ]]; then
        matched_count=$(ls ${NETSIM_DIR} | grep -v .zip | grep -E "(^|\s)${val}($|\s)" | wc -l)
    else
        matched_count=$(ls ${NETSIM_DIR} | grep -v .zip | grep -w ${val} | wc -l)
    fi
    
    if [[ ${matched_count} -gt 1 ]]; then
        log "ERROR: Multiple simulation found having with name or id ${val} in it's name."
    fi
}

validateSims

