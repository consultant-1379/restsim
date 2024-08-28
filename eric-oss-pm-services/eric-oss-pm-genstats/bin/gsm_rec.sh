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
# Version no    :  NSS 21.12
# Purpose       :  Script is responsible for generating files for Events for GSM sims
# Jira No       :  NSS-35593
# Gerrit Link   :
# Description   :  File Size change for BSC Recordings for Thin Layer BSC
# Date          :  14/05/2021
# Last Modified :  kumar.dhiraj7@tcs.com
####################################################

# To maitain mtr and bsc recs tmpfile deletion in /netsim_users/pms/etc/ directory
maintainance(){
    if [[ -f ${TMP_GSM_EVENT_FILE} ]]; then
	    rm -f ${TMP_GSM_EVENT_FILE}
    fi
}

# This function will be responsible for generation of MTR file for particular BSC nodes
generateMtrFile() {
    sim_name=$1
    node_name=$2

    if  [[ ! -z ${GSM_MSC_BSC_MTR_FILE_DIR} ]];then
        dest_file_path="${SIM_DIR}/${sim_name}/${node_name}/${GSM_MSC_BSC_MTR_FILE_DIR}"
    else
        log "ERROR : GSM_MSC_BSC_MTR_FILE_DIR value is empty in netsim_cfg file. Please provide path for file generation."
    fi
    data_file_path="${SIM_DIR}/${sim_name}/${node_name}/fs/mgbridata.txt"

    count=`get_count "MTR" ${sim_name} ${node_name}`

    if [[ -f ${data_file_path} ]];then
        log "INFO : BSC MTR :${data_file_path} found. Checking valid RR keys sim: ${sim_name} node:${node_name}"
        rr_list=($(cat ${data_file_path} | awk 'BEGIN{n=3}NR<=n{next}1 {print $3}'))

        if [[ ${#rr_list[@]} -gt 0 ]];then
            for RR_key in ${rr_list[@]};do
                padded_count=`printf "%04d\n" ${count}`
                if  [[ ${RR_key} -ge 0 ]] && [[ ${RR_key} -le 63 ]];then
                    padded_RR_key=`printf "%02d\n" ${RR_key}`
                    create_link_file ${input_mtr_path} ${dest_file_path} MTRFIL${padded_RR_key}-${padded_count}
                    if [[ $? -eq 0 ]];then
                        log "INFO : MTR file generation for sim: ${sim_name} node:${node_name} with RR:${RR_key} is successful"
                    fi
                else
                    log "WARNING : Invalid RR:${RR_key}.Skipping MTR file generation for sim: ${sim_name} node:${node_name} with RR:${RR_key}"
                fi
            done
            mv ${count_dir}/${sim_name}_MTR_${node_name}_${count} ${count_dir}/${sim_name}_MTR_${node_name}_$(($count+1))
        else
            log "WARNING : No RR keys found for sim ${sim_name} node:${node_name}"
        fi
    fi
}

# This function will be responsible for generation of EVENT files for particular BSC nodes
generateGSMrecs(){
    sim_name=$1
    node_name=$2

    check_files_path="${SIM_DIR}/${sim_name}/${node_name}/fs/"
    node_path="${SIM_DIR}/${sim_name}/${node_name}"

    if [[ ${TYPE} == "NRM5.1" ]] && [[ ${node_name} == ${EIGHT_K_BSC} ]]; then
        input_mrr_path=${input_thin_bsc_mrr_path}
        input_bar_path=${input_thin_bsc_bar_path}
        input_cer_path=${input_thin_bsc_cer_path}
    fi

    rec_count=`get_count "RECS" ${sim_name} ${node_name}`
    rec_enabled_list=($(ls ${check_files_path} | egrep "MRR.txt|BAR.txt|RIR.txt|CTR.txt|CER.txt" | cut -d"." -f1))

    if [[ ${#rec_enabled_list[@]} -gt 0 ]];then
        padded_rec_count=`printf "%04d\n" ${rec_count}`
        for rec in ${rec_enabled_list[@]}; do
            log "INFO : BSC ${rec} : ${rec}.txt found. Generating ${rec} for sim: ${sim_name} node:${node_name}"
            if [[ ${rec} == "MRR" ]] && [[ ! -z ${GSM_BSC_MRR_FILE_DIR} ]];then
                dest_file_path="${node_path}/${GSM_BSC_MRR_FILE_DIR}"
                create_link_file ${input_mrr_path} ${dest_file_path} MRRFIL00-${padded_rec_count}
            elif [[ ${rec} == "BAR" ]] && [[ ! -z ${GSM_BSC_BAR_FILE_DIR} ]]; then
                dest_file_path="${node_path}/${GSM_BSC_BAR_FILE_DIR}"
                create_link_file ${input_bar_path} ${dest_file_path} BARFIL00-${padded_rec_count}
            elif [[ ${rec} == "CER" ]] && [[ ! -z ${GSM_BSC_CER_FILE_DIR} ]]; then
                dest_file_path="${node_path}/${GSM_BSC_CER_FILE_DIR}"
                create_link_file ${input_cer_path} ${dest_file_path} CERFIL00-${padded_rec_count}
            elif [[ ${rec} == "CTR" ]] && [[ ! -z ${GSM_BSC_CTR_FILE_DIR} ]]; then
                dest_file_path="${node_path}/${GSM_BSC_CTR_FILE_DIR}"
                create_link_file ${input_ctr_path} ${dest_file_path} CTRFILE-${padded_rec_count}
            elif [[ ${rec} == "RIR" ]] && [[ ! -z ${GSM_BSC_RIR_FILE_DIR} ]]; then
                dest_file_path="${node_path}/${GSM_BSC_RIR_FILE_DIR}"
                create_link_file ${input_rir_path} ${dest_file_path} RIRFIL00-${padded_rec_count}
            fi
            if [[ $? -eq 0 ]];then
                log "INFO : ${rec} file generation for sim: ${sim_name} node:${node_name} is successful"
            fi
        done
        mv ${count_dir}/${sim_name}_RECS_${node_name}_${rec_count} ${count_dir}/${sim_name}_RECS_${node_name}_$(($rec_count+1))
    fi
}

create_link_file(){
    inp_rec_file=$1
    out_rec_dir=$2
    output_file=$3

    if ! [[ -d ${out_rec_dir} ]]; then
          mkdir -p ${out_rec_dir}
          mkdir -p ${out_rec_dir}/../Delete
          mkdir -p ${out_rec_dir}/../Send
          mkdir -p ${out_rec_dir}/../Archive
    fi
    ln -s ${inp_rec_file} ${out_rec_dir}/${output_file}
    if [[ $? -eq 0 ]];then
         log "INFO : File generation for output file: ${output_file} is successful"
    fi
}

get_count(){
    filetype=$1
    sim_name=$2
    node_name=$3
    count=`ls ${count_dir} | grep ${sim_name}_${filetype}_${node_name}_ | rev | cut -d"_" -f1 | rev`

    if [[ -z ${count} ]];then
        count=1
        touch ${count_dir}/${sim_name}_${filetype}_${node_name}_${count}
    elif [[ ${count} -gt 9999 ]];then
        mv ${count_dir}/${sim_name}_${filetype}_${node_name}_${count} ${count_dir}/${sim_name}_${filetype}_${node_name}_1
        count=1
    fi
    echo ${count}
}

#
#Main
#

#source ROP period
source_rop_min=$1
is_hc=$2

# Need to source this first to get out_dir paths
if [ -r /netsim/netsim_cfg ] ; then
    . /netsim/netsim_cfg > /dev/null 2>&1
fi

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions

SIM_DIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"
SANDBOX_TEMPLATE_DIR="/netsim_users/pms/sandbox_templates"
TMP_GSM_EVENT_FILE="/netsim_users/pms/etc/.GSM_EVENTS"
#INPUT LOCATIONS
input_mtr_path="${SANDBOX_TEMPLATE_DIR}/BSC/MTR/MTRFIL00-0005"
input_bar_path="${SANDBOX_TEMPLATE_DIR}/BSC/BAR/BARFIL00-0001"
input_mrr_path="${SANDBOX_TEMPLATE_DIR}/BSC/MRR/MRRFIL00-0004"
input_cer_path="${SANDBOX_TEMPLATE_DIR}/BSC/CER/CERFIL00-0002"
input_ctr_path="${SANDBOX_TEMPLATE_DIR}/BSC/CTR/CTRFILE-0003"
input_rir_path="${SANDBOX_TEMPLATE_DIR}/BSC/RIR/RIRFIL00-0006"
#Thin Layer 8K recordings path
input_thin_bsc_bar_path="${SANDBOX_TEMPLATE_DIR}/BSC/BSC_THIN_LAYER/BAR/BARFIL00-0000000008"
input_thin_bsc_mrr_path="${SANDBOX_TEMPLATE_DIR}/BSC/BSC_THIN_LAYER/MRR/MRRFIL00-0000000005"
input_thin_bsc_cer_path="${SANDBOX_TEMPLATE_DIR}/BSC/BSC_THIN_LAYER/CER/CERFIL01-0000000008"

count_dir=/netsim_users/.count
if [[ ! -d ${count_dir} ]];then
    mkdir ${count_dir}
fi

log "INFO: Initializing GSM EVENTS FILE generation"
for gsm_rec_info in `cat ${TMP_GSM_EVENT_FILE}`; do
    file_type=`echo ${gsm_rec_info} | awk -F':' '{print $3}'`
    rop_min=`echo ${gsm_rec_info} | awk -F':' '{print $4}'`
    if [[ ${source_rop_min} == ${rop_min} ]] || [[ ${is_hc} == "YES" ]];then
        if [[ ${file_type} == "MTR" ]];then
            generateMtrFile "$(echo ${gsm_rec_info} | awk -F':' '{print $1}')" "$(echo ${gsm_rec_info} | awk -F':' '{print $2}')"
        else
            generateGSMrecs "$(echo ${gsm_rec_info} | awk -F':' '{print $1}')" "$(echo ${gsm_rec_info} | awk -F':' '{print $2}')"
        fi
	fi
done
log "INFO: GSM EVENTS FILE generation completed."

if [[ ${source_rop_min} == ${rop_min} ]] || [[ ${is_hc} == "YES" ]];then
    maintainance
fi



