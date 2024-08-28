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
# Version no    :  NSS 22.05
# Purpose       :  The purpose of this script to distribute files amongst respective child scripts.
# Jira No       :  NSS-35517
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/11675757/
# Description   :  Adding 20mb file support for SCEF in MD_1
# Date          :  29/01/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

PM_DIR=${1}
APPEND_PATH=${2}
NE_TYPE=${3}
FILE_FORMAT=${4}
OUTPUT_TYPE=${5}
INPUT_LOCATION=${6}
DATE=${7}
ROP_START_TIME=${8}
ROP_END_TIME=${9}
LOG=${10}
PROCESS_TYPE=${11}
SCRIPT=${12}
ROP_PERIOD=${13}
ROP_END_DATE=${14}
epoch_rop_folder=${17}
LOCK_FILE=${18}

DEPL_TYPE=$(cat /netsim/netsim_cfg | grep -v '#' | grep 'TYPE=' | awk -F'"' '{print $2}')

if [[ $NE_TYPE == *"SCEF"* ]]; then
    FILE_TYPE=${15}
elif [[ $NE_TYPE == *"gNodeBRadio"* ]]; then
    HARDWARE_NAME=${15}
fi

INSTALL_DIR_NAME=`dirname $0`
INSTALL=`cd ${INSTALL_DIR_NAME} ; pwd`

targetDir=$LOG/$NE_TYPE"_"$PROCESS_TYPE"_"$ROP_PERIOD
if [ ! -d "$targetDir" ]; then
        mkdir -p $targetDir
fi

completeOutDirsList="$targetDir/allOutputDirslist"

if [ ! -f ${completeOutDirsList} ]; then
   ls $PM_DIR/ | grep $NE_TYPE | sort > $completeOutDirsList
fi

completeMappedFileList="$targetDir/mappedFilelist"
mappedFileListScefA="$targetDir/mappedFilelistA"
mappedFileListScefB="$targetDir/mappedFilelistB"

arrayOfInputFiles=( `ls $INPUT_LOCATION` )
#Handling for SCEF nodes to reduce load on cpu
#We have to zip files only once and then copy
if [[ ${NE_TYPE} == *"SCEF"* ]] && [[ ${FILE_TYPE} == A ]];then
    sourceDir=${INPUT_LOCATION}
    outDir=${INPUT_LOCATION}/.tmpScefFiles
    if ! [[ -d ${outDir} ]];then
        mkdir -p ${outDir}
    else
        rm -f ${outDir}/*
    fi
    cp -r ${sourceDir}/* ${outDir}/
    tmp_src_dirs=`ls ${outDir} | grep -v ".zip"`
    for dir in ${tmp_src_dirs};do
        file_list=''
        file_time_stamp=A${DATE}.${ROP_START_TIME}-${ROP_END_TIME}
        for file in `ls ${outDir}/$dir`;do
           mv ${outDir}/${dir}/${file} ${outDir}/${dir}/${file_time_stamp}_${file}
        done
        zip -j ${outDir}/${dir}.zip ${outDir}/${dir}/* > /dev/null
        if [[ $? -ne 0 ]];then
           echo "Issue while creation of zips folders\nexiting process"
           exit 1
        fi
        rm -rf ${outDir}/${dir}
    done
    arrayOfInputFiles=( `ls $outDir` )
fi  
index=0
for outDir in `cat ${completeOutDirsList}`;do
    if [[ $NE_TYPE == *"SCEF"* ]];then
        if [[ ${FILE_TYPE} == A ]]; then
            inputLen=$(( ${#arrayOfInputFiles[@]} - 1 ))
            if [[ ${inputLen} -gt 29 ]];then
                  inputLen=29
            fi
            for count in  $(seq 0 ${inputLen}) ;do
               echo ${arrayOfInputFiles[$count]}";"$outDir";"A_SCEF >> $mappedFileListScefA
            done
        elif [[ ${FILE_TYPE} == B ]]; then
            echo ${arrayOfInputFiles[$index]}";"$outDir >> $mappedFileListScefB
            index=$((index+1))
            last_idx=$(( ${#arrayOfInputFiles[@]} - 1 ))
            if [ $index -gt $last_idx ];then
               index=0
            fi
        fi
    else
        echo ${arrayOfInputFiles[$index]}";"$outDir >> $completeMappedFileList
        index=$((index+1))
        last_idx=$(( ${#arrayOfInputFiles[@]} - 1 ))
        if [ $index -gt $last_idx ];then
           index=0
        fi
    fi
done 

if [[ $NE_TYPE == *"SBG-IS"* ]]; then
    UNIQUE_ID=${15}
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "$UNIQUE_ID" &

elif [[ $NE_TYPE == *"HSS-FE-TSP"* ]] || [[ $NE_TYPE == *"MTAS-TSP"* ]] || [[ $NE_TYPE == *"CSCF-TSP"* ]] || [[ $NE_TYPE == *"SAPC-TSP"* ]] ; then
    MEASUREMENT_JOB_NAME=${15}
    TSP_MPID_TIME_START_DATETIME=${16}
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "${MEASUREMENT_JOB_NAME}" "$TSP_MPID_TIME_START_DATETIME" &

elif [[ $NE_TYPE == *"FrontHaul"* ]]; then
    FILE_beginTime=${15}
    FILE_endTime=${16}
    dur=${17}
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "$FILE_beginTime" "$FILE_endTime" "$dur" &

elif [[ $NE_TYPE == *"EIR-FE"* ]] || [[ $NE_TYPE == *"VCUDB"* ]]; then
    MEASUREMENT_JOB_NAME=${15}
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "${MEASUREMENT_JOB_NAME}" &

elif [[ $NE_TYPE == *"SCEF"* ]]; then
        if [[ ${FILE_TYPE} == B ]];then
            /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$mappedFileListScefB" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "${FILE_TYPE}" 
        else
            if [[ ${DEPL_TYPE} != "MD_1" ]]; then
               INPUT_LOCATION=${INPUT_LOCATION}/.tmpScefFiles/ 
            fi
            /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$mappedFileListScefA" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "${FILE_TYPE}"
        fi
elif [[ $NE_TYPE == *"gNodeBRadio"* ]]; then
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "${HARDWARE_NAME}"
else
    /${INSTALL}/$SCRIPT "$PM_DIR" "$APPEND_PATH" "$NE_TYPE" "$FILE_FORMAT" "$OUTPUT_TYPE" "$INPUT_LOCATION" "$DATE" "$ROP_START_TIME" "$ROP_END_TIME" "$INSTALL" "$LOG" "$completeMappedFileList" "$PROCESS_TYPE" "$ROP_PERIOD" "$ROP_END_DATE" "" "" "" "${epoch_rop_folder}"  "${LOCK_FILE}" &
fi

