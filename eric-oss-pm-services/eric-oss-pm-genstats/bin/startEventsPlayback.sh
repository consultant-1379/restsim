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
# Version no    :  NSS 17.10
# Purpose       :  The purpose of this script to call playbackGenerator framework to generate EVENTS PM files.
# Jira No       :  NSS-12596
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2333640/
# Description   :  Genstats - Fronthaul Simulation Delivery - Updated PM model + port change
# Date          :  01/06/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################

#Fetching input arguments
PM_DIR=${1}
APPEND_PATH=${2}
NE_TYPE=${3}
FILE_FORMAT=${4}
OUTPUT_TYPE=${5}
INPUT_LOCATION=${6}
DATE=${7}
ROP_START_TIME=${8}
ROP_END_TIME=${9}
INSTALL_DIR=${10}
LOG=${11}
FINAL_MAPPED_FILE=${12}
PROCESS_TYPE=${13}
ROP_PERIOD=${14}
ROP_END_DATE=${15}

LOOP_INSTANCE=1

generateEventsFile(){
	
	NEW_FILE_NAME=$(echo ${BCK_FILE_FORMAT} | sed "s/DATE/$DATE/; s/ROP_START_TIME/$ROP_START_TIME/; s/ROP_END_TIME/$ROP_END_TIME/; s/ROP_END_DATE/$ROP_END_DATE/; s/MANAGED_ELEMENT_ID/$targetDir/")
	
	outputFile=${OUTPUT_PATH}/$NEW_FILE_NAME
	
	for(( inst=1; inst <= ${LOOP_INSTANCE}; inst++ )); do
	
    	if [ $OUTPUT_TYPE == "COPY" ]; then
                /${INSTALL_DIR}/playbackGenerator.sh $sourceFile $outputFile -c &
        elif [ $OUTPUT_TYPE == "ZIP" ]; then
                /${INSTALL_DIR}/playbackGenerator.sh $sourceFile $outputFile -g &
        else
                /${INSTALL_DIR}/playbackGenerator.sh $sourceFile $outputFile -l &
        fi
	done
}

for fname in `cat $FINAL_MAPPED_FILE`; do
        targetDir=`echo $fname | cut -d";" -f2`
        sourceFile=${INPUT_LOCATION}/$(echo $fname | cut -d";" -f1)
         
        OUTPUT_PATH=$PM_DIR/$NE_TYPE/$targetDir/fs/$APPEND_PATH
        
        if [[ ${APPEND_PATH} == *"fs"* ]];then
            OUTPUT_PATH=$PM_DIR/$NE_TYPE/$targetDir/$APPEND_PATH
        fi
        
        if [ ! -d ${OUTPUT_PATH} ];then
            mkdir -p ${OUTPUT_PATH}
        fi
        
        generateEventsFile
done

