#!/bin/bash
###############################################################################
###############################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###############################################################################
###############################################################################

###################################################
# Version no    :  NSS 17.11
# Purpose       :  This script is responsible for pre-health checks of Genstats including all nodes in sims are in STARTED state or not and SCANNER state of all sims at location /netsim/netsim_dbdir/simdir/netsim/netsimdir/
# Jira No       :  NA
# Gerrit Link   :  NA
# Description   :  Updated to add support for checking started sim availability in /pms_tmpfs.
# Date          :  06/21/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################

#Constants Declaration
INSTALL_DIR=`dirname $0`
INSTALL_PATH=`cd ${INSTALL_DIR} ; pwd`
TEMP=/tmp
PMDIR=/pms_tmpfs
NETSIMDIR=/netsim/netsim_dbdir/simdir/netsim/netsimdir/
LOG_FILE="/$INSTALL_PATH/preHealthCheckGenstats.log"
SIM_LIST=""
SUPPORTED_NE_TYPES="CSCF EPG-EVR EPG-SSR MGW MTAS LTE MSRBS-V1 MSRBS-V2 PRBS ESAPC SBG SGSN SPITFIRE TCU RBS RNC RXI VBGF HSS-FE IPWORKS C608 MRF UPG WCG VPP VRC RNNODE DSC WMG SIU EME"

#Variables Declaration
printBlankLineFlag=false
failureFlag=false

#This method is used to log input messages
log(){
    msg=$1
        timestamp=`date +%H:%M:%S`
        MSG="${timestamp} ${msg}"

    echo $MSG >> $LOG_FILE
        echo $MSG
}

#This method is used to print blank lines for simplicity of console output.
printBlankLines(){
    flag=$1
    if [ $flag = true ];then
            printf "\n\n\n\n"
            printBlankLineFlag=false;
    fi
}

#Main

if [ ! -d $TEMP ];then
   mkdir -p $TEMP
fi

if [ ! -d $PMDIR ];then
    log "ERROR: $PMDIR does not exist."
    exit 1
fi

if [ ! -d $NETSIMDIR ];then
    log "ERROR: $NETSIMDIR does not exist."
    exit 1
fi

#Get the started nodes information in temporary file
echo ".show started" | /netsim/inst/netsim_shell > $TEMP/startedNodesDetails.txt

log "INFO: Start Processing"
for sim in `ls $PMDIR | egrep -v "TCU02|SIU02|BSC|FrontHaul|xml_step|TSP|CORE-MGW-15B-16A-UPGIND-V1|CORE-SGSN-42A-UPGIND-V1|PRBS-99Z-16APICONODE-UPGIND-MSRBSV1-LTE99|RNC-15B-16B-UPGIND-V1|VNFM|LTEZ9334-G-UPGIND-V1-LTE95|LTEZ8334-G-UPGIND-V1-LTE96|LTEZ7301-G-UPGIND-V1-LTE97|RNCV6894X1-FT-RBSU4110X1-RNC99|LTE17A-V2X2-UPGIND-DG2-LTE98|LTE16A-V8X2-UPGIND-PICO-FDD-LTE98|TLS|VTFRADIONODE|5GRADIONODE|VSD"`;do

    #Check in /pms_tmpfs/ for started nodes exists or not.
    for node in `ls $PMDIR/$sim`;do
        grep "$node" $TEMP/startedNodesDetails.txt > /dev/null
        if [ ! $? -eq 0 ] ; then
            if [ $failureFlag = false ];then
                 failureFlag=true;
            fi
            log "ERROR: Node $node is not in started state.Please start or delete $node directory from $PMDIR/$sim"
            if [ $printBlankLineFlag = false ];then
                 printBlankLineFlag=true;
            fi
        fi
    done

printBlankLines $printBlankLineFlag

done

#For MME,FrontHaul and BSC simulations need to check in location /netsim/netsim_dbdir/simdir/netsim/netsimdir/.

for sim in `ls $NETSIMDIR | egrep "SGSN" | egrep -v 'TSP|CORE-MGW-15B-16A-UPGIND-V1|CORE-SGSN-42A-UPGIND-V1|PRBS-99Z-16APICONODE-UPGIND-MSRBSV1-LTE99|RNC-15B-16B-UPGIND-V1|VNFM|LTEZ9334-G-UPGIND-V1-LTE95|LTEZ8334-G-UPGIND-V1-LTE96|LTEZ7301-G-UPGIND-V1-LTE97|RNCV6894X1-FT-RBSU4110X1-RNC99|LTE17A-V2X2-UPGIND-DG2-LTE98|LTE16A-V8X2-UPGIND-PICO-FDD-LTE98|TLS|VTFRADIONODE|5GRADIONODE|VSD'`;do

    #Check in /netsim/netsim_dbdir/simdir/netsim/netsimdir/ for started nodes exists or not.
    for node in `ls $NETSIMDIR/$sim`;do
        grep "$node" $TEMP/startedNodesDetails.txt > /dev/null
        if [ ! $? -eq 0 ] ; then
            if [ $failureFlag = false ];then
             failureFlag=true;
            fi
            log "ERROR: Node $node is not in started state.Please start or delete $node directory from $NETSIMDIR/$sim"
            if [ $printBlankLineFlag = false ];then
             printBlankLineFlag=true;
            fi
        fi
    done

printBlankLines $printBlankLineFlag

done


#Check started SIM are present in /pms_tmpfs or not.
SIM_LIST="$(ls $PMDIR | grep -v xml_step)"

for ne_type in ${SUPPORTED_NE_TYPES}; do
    for sim in `ls $NETSIMDIR | grep -i ${ne_type}`;do
        grep "$sim" $TEMP/startedNodesDetails.txt > /dev/null
            if [ $? -eq 0 ] ; then
                if [[ ${sim} == *"LTE"* && ${sim} != *"TLS"* ]] || [[ ${sim} == *"RNC"* ]];then
                        sim_bck=`echo ${sim} | rev | cut -d'-' -f1 | rev`
                        if [[ ${sim_bck} == *"LTE"* || ${sim_bck} == *"RNC"* ]];then
                            sim=${sim_bck}
                        fi
                fi
                echo "${SIM_LIST}" | grep $sim > /dev/null
                if [ $? -ne 0 ] ; then
                    if [ $failureFlag = false ];then
                        failureFlag=true;
                    fi
                    log "ERROR: SIM $sim is in started state,but $sim directory is not present in /pms_tmpfs."
                    if [ $printBlankLineFlag = false ];then
                        printBlankLineFlag=true;
                    fi
                fi
            fi
    done
done

#Check the scanners for simulators whether ACTIVE or not

for sim in `ls $NETSIMDIR`;do

/netsim/inst/netsim_pipe <<EOF | grep -i "\<ACTIVE\>" > $TEMP/scannerDetailsCheck.txt
.open ${sim}
.select network
showscanners2;
EOF

if [ -s $TEMP/scannerDetailsCheck.txt ];then
        if [ $failureFlag = false ];then
        failureFlag=true;
        fi
        log "ERROR: Scanner for nodes in simulator ${sim} is in ACTIVE state.Please change the scanner state to SUSPENDED."
        if [ $printBlankLineFlag = false ];then
                printBlankLineFlag=true;
        fi
fi

printBlankLines $printBlankLineFlag

done

#Removing temporary files
rm -rf $TEMP/startedNodesDetails.txt $TEMP/scannerDetailsCheck.txt

if [ $failureFlag = true ];then
        log "ERROR: Pre-Health Check Failed."
else
        log "INFO: Pre-Health Check Completed Successfully."
fi
log "INFO: End Processing"
