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
# Version no    :  NSS 21.05
# Purpose       :  The purpose of this script to copy and link source to target file.
# Jira No       :  NSS-35517
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/11675757/
# Description   :  Adding 20mb file support for SCEF in MD_1
# Date          :  29/01/2022
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

source=$1
target=$2
type=$3
NE_TYPE=$4
ROP_PERIOD=$5
NODE_NAME=$6

if [[ $NE_TYPE == *"FrontHaul"* ]]; then
    FILE_beginTime=$7
    FILE_endTime=$8
    dur=$9
elif [[ $NE_TYPE == *"SCEF"* ]] || [[ $NE_TYPE == *"vAFG"* ]]; then
    START_DATE=$7
    START_TIME=$8
    END_TIME=$9
fi

TIMESTAMP_FILE="/netsim_users/pms/etc/.playback_node_timestamp_${ROP_PERIOD}_min"
DEPL_TYPE=$(cat /netsim/netsim_cfg | grep -v '#' | grep 'TYPE=' | awk -F'"' '{print $2}')

#Logic for handling NE types that require timestamp updation in the file
TSP_TIMESTAMP_NE_LIST="HSS-FE-TSP MTAS-TSP CSCF-TSP SAPC-TSP"
TSP_START_TIME_STAMP=`grep "TSP" ${TIMESTAMP_FILE} | awk -F";" '{print $2}'`
TSP_END_TIME_STAMP=`grep "TSP" ${TIMESTAMP_FILE} | awk -F";" '{print $3}'`
CPP_START=`grep "CPP" ${TIMESTAMP_FILE} | awk -F";" '{print $2}'`
CPP_END=`grep "CPP" ${TIMESTAMP_FILE} | awk -F";" '{print $3}'`
BSP_START=`grep "BSP" ${TIMESTAMP_FILE} | awk -F";" '{print $2}'`
BSP_END=`grep "BSP" ${TIMESTAMP_FILE} | awk -F";" '{print $3}'`
BSP_START=${BSP_START%+*}
BSP_END=${BSP_END%+*}

log() {
    MSG=$1

    TS=`date +"%Y-%m-%d %H:%M:%S"`
    echo "${TS} ${MSG}"
}

update_me_context(){
   FILE=$1
   OLD_ME_CONTEXT=$2
   
   sed -i -e "s/localDn=\"${OLD_ME_CONTEXT}\"/localDn=\"${NODE_NAME}\"/g" ${FILE}
}

update_timestamp(){
    NE=$1
    target=$2
    NE_START=$3
    NE_END=$4
    
    TEMPLATE_START_TIME=`cat $target | grep beginTime | awk -F'"' '{print $2}'`
    TEMPLATE_END_TIME=`cat $target | grep endTime | head -1 | awk -F'"' '{print $4}'`
    sed -i -e "s/beginTime=\"${TEMPLATE_START_TIME}\"/beginTime=\"${NE_START}\"/g" -e "s/endTime=\"${TEMPLATE_END_TIME}\"/endTime=\"${NE_END}\"/g" $target
}

updateSourceFilesForZip(){
   sourceDir=$1
   outDir=$2
   fileList=''
   for file in `ls ${sourceDir}`;do
      cp ${sourceDir}/${file} ${outDir}/A${START_DATE}.${START_TIME}-${END_TIME}_${file}
      fileList=$fileList" ${outDir}/A${START_DATE}.${START_TIME}-${END_TIME}_${file}"
   done
}

createFilesForTar(){
    sourceFile=$1
    outDir=$2
    node_name=$3
    fileList=''
    for fileNameFullPath  in $sourceFile; do
        jobId=`basename "$fileNameFullPath"`
        fileName="A${START_DATE}.${START_TIME}-${END_TIME}-${jobId}.${node_name}.xml"
        cp ${fileNameFullPath} ${outDir}/${fileName}
        fileList=${fileList}" "${fileName}
    done
}

if [ $type == "-c" ]; then
    if [ ! -f $target ]; then
        # copy for all depl types except MD_1 as we are using symbolik links
        cp $source $target 2>/dev/null
        if [[ $? == 0 && $NE_TYPE == *"gNodeBRadio"* ]]; then
            log "ORU PM Generation success : $target"   
        fi
    fi 


elif [ $type == "-g" ];then
    if [[ ${DEPL_TYPE} == "DO" ]];then
        cp ${source} ${target}
        update_timestamp $NE_TYPE $target ${CPP_START} ${CPP_END}
        if [[ $NE_TYPE == *"EPG-OI"*  ]]; then
            update_me_context ${target} "selnpcnepg08"
        elif [[ ${NE_TYPE} == *"vWMG-OI"* ]];then
            update_me_context ${target} "ManagedElement=1"
        fi
        gzip -c ${target} > ${target}.gz
        rm -f ${target}

    elif [[ ${DEPL_TYPE} == "NSS" ]];then   
        if [[ $NE_TYPE == *"EPG-OI"*  ]]; then
            #Here input is uncompressed xml and we update time stamp inside file
            cp $source $target
            update_timestamp $NE_TYPE $target ${CPP_START} ${CPP_END}
            gzip -c $target > $target.gz
            rm -f $target
        else
            gzip -c $source > $target.gz

        fi

    else
            if [[ $NE_TYPE == *"EPG-OI"*  ]]; then
                #Here input is compressed gzip xml and create hardlink
                ln -f $source $target.gz
            else   
                gzip -c $source > $target.gz
            fi
    fi


elif [ $type == "-s" ] ||  [ $type == "-sg" ];then
if [[ $NE_TYPE == *"FrontHaul"* ]]; then
    if [[ $dur == "900" ]]; then
        sed -e "s/beginTime=\"2017-07-19T12:45:01+03:00\"/beginTime=\"${FILE_beginTime}\"/g" -e "s/endTime=\"2017-07-19T12:45:59+03:00\"/endTime=\"${FILE_endTime}\"/g" -e "s/endTime=\"2017-07-19T13:00:01+03:00\"/endTime=\"${FILE_endTime}\"/g" $source > $target
    elif [[ $dur == "60" ]]; then
        sed -e "s/beginTime=\"2017-07-19T12:45:01+03:00\"/beginTime=\"${FILE_beginTime}\"/g" -e "s/endTime=\"2017-07-19T12:45:59+03:00\"/endTime=\"${FILE_endTime}\"/g" -e "s/endTime=\"2017-07-19T13:00:01+03:00\"/endTime=\"${FILE_endTime}\"/g" -e "s/jobId=\"PRIMARY15MIN\"/jobId=\"PRIMARY1MIN\"/g" -e "s/duration=\"PT900S\"/duration=\"PT60S\"/g" $source > $target
    else
        sed -e "s/beginTime=\"2017-07-19T12:45:01+03:00\"/beginTime=\"${FILE_beginTime}\"/g" -e "s/endTime=\"2017-07-19T12:45:59+03:00\"/endTime=\"${FILE_endTime}\"/g" -e "s/endTime=\"2017-07-19T13:00:01+03:00\"/endTime=\"${FILE_endTime}\"/g" -e "s/jobId=\"PRIMARY15MIN\"/jobId=\"PRIMARY1440MIN\"/g" -e "s/duration=\"PT900S\"/duration=\"PT86400S\"/g" $source > $target
    fi
fi
    if [ $type == "-sg" ];then
        if [[ $NE_TYPE == *"BSP"* ]] ; then
            cp $source $target 2>/dev/null
            update_timestamp $NE_TYPE $target $BSP_START $BSP_END
        fi

        gzip -c $target > $target.gz
        rm -rf $target
    fi
elif [ $type == "-z" ];then
    updateSourceFilesForZip $source $(dirname "${target}")
    zip -j $target.zip `echo $fileList` > /dev/null 
    rm -f `echo $fileList`
elif [ $type == '-t' ];then
    createFilesForTar "${source}" $(dirname "${target}") $NODE_NAME
    fileGenerationMinutes=$(date +"%H%M")
    # packs generated xml PM files into a tar.gz file and removes those xml files from the dir in which they were packed
    tar --remove-files -czvf  "${target}_${START_DATE}-${fileGenerationMinutes}.tar.gz"  -C $(dirname "${target}")  `echo $fileList` > /dev/null
else
    ln -sf $source $target
    rc=$?
    if [ $rc -ne 0 ] ; then
        if [ $rc -eq 2 ] ; then
            log "INFO: File exists: $target"
        else
            log "ERROR: Failed to link $target"
        fi
    fi
fi

for TSP_NE in ${TSP_TIMESTAMP_NE_LIST}; do
    if [[ $NE_TYPE == *"${TSP_NE}"* ]]; then
        sed -i "s#<cbt>\([^<][^<]*\)</cbt>#<cbt>${TSP_START_TIME_STAMP}</cbt>#" $target
        sed -i "s#<mts>\([^<][^<]*\)</mts>#<mts>${TSP_END_TIME_STAMP}</mts>#" $target
        sed -i "s#<ts>\([^<][^<]*\)</ts>#<ts>${TSP_END_TIME_STAMP}</ts>#" $target
        break
    fi
done

# Updating files that are generated uncompressed
TIMESTAMP_NE_LIST="SBG-IS EIR-FE"
for NE  in ${TIMESTAMP_NE_LIST}; do
    if [[ $NE_TYPE == *"${NE}"* ]]; then
      NE_START="$NE"_START
      NE_END="$NE"_END
      update_timestamp $NE $target ${CPP_START} ${CPP_END}
    fi
done
