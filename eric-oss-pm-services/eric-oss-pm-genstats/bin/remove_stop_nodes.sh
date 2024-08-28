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
# Version no    :  NSS 17.13
# Purpose       :  Remove directory of simulation and nodes which are not present in /tmp/showstartednodes.txt file.
# Jira No       :  NSS-10222
# Gerrit Link   :
# Description   :  Support fot G+W+L RNC sims.
# Date          :  1/08/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

started_node_file="/tmp/showstartednodes.txt"
c_pm_dir="/c/pm_data/"
pms_dir="/pms_tmpfs/"
netsim_dbdir="/netsim/netsim_dbdir/simdir/netsim/netsimdir/"

pms_sim_list=($(ls ${pms_dir} | grep -v xml_step))

. /netsim_users/pms/bin/functions

remove_directory() {
    sim_name=$1
    duplicate_pms_sim=$2
    for pms_sim in ${duplicate_pms_sim}; do
        if grep -q ${pms_sim} ${started_node_file}; then
            node_list=($(ls ${pms_dir}${sim_name}))
            if [ ! -z "${node_list}" ] ; then
                for node_name in ${node_list[@]}; do
                    if [[ ${node_name} == *"RNC"* ]]; then
                        if [[ ${node_name} == *"BSC"* ]]; then
                            continue
                        fi
                        if [[ "${node_name}" == "${sim_name}" ]]; then
                            cat ${started_node_file} | grep -w "${node_name}" | grep "netsimdir" | awk -F' ' '{print $1}' | egrep -v -i 'RBS|BSC' > /dev/null
                            if [[ $? -eq 0 ]]; then
                                continue
                            else
                               log "INFO: Deleting ${pms_dir}${sim_name}/${node_name}"
                               rm -r "${pms_dir}${sim_name}/${node_name}"
                            fi
                        else
                            cat ${started_node_file} | grep -w "${node_name}" > /dev/null
                            if [[ $? -eq 0 ]]; then
                                continue
                            else
                                log "INFO: Deleting ${pms_dir}${sim_name}/${node_name}"
                                rm -r "${pms_dir}${sim_name}/${node_name}"
                            fi
                        fi
                    else
                        if grep -q ${node_name} ${started_node_file}; then
                            continue
                        else
                            log "INFO: Deleting ${pms_dir}${sim_name}/${node_name}"
                            rm -r "${pms_dir}${sim_name}/${node_name}"
                        fi
                    fi
                done
            else
                log "INFO: Deleting ${pms_dir}${sim_name}"
                rm -r "${pms_dir}${sim_name}"
            fi
        else
            log "INFO: Deleting ${pms_dir}${sim_name}"
            rm -r "${pms_dir}${sim_name}"
        fi
    done
}


#Main
if [ -f ${started_node_file} ]; then
    if grep -q "restart_netsim" ${started_node_file}; then
        log "WARN: netsim is down. Exiting process."
        exit 1
    fi
    for pms_sim in ${pms_sim_list[@]}; do
        sim_name=${pms_sim}
        if [[ ${pms_sim} == *"LTE"* ]] || [[ ${pms_sim} == *"RNC"* ]]; then
            db_sim_name=$(ls ${netsim_dbdir} | grep ${pms_sim})
            if [ ! -z "${db_sim_name}" ] ; then
                pms_sim=${db_sim_name}
            fi
        fi
        remove_directory ${sim_name} ${pms_sim}
    done
    log "INFO: Deletion of not started nodes is completed."
else
    log "WARN: ${started_node_file} file not found."
fi
