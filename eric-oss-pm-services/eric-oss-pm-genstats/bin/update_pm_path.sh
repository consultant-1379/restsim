#!/bin/bash

. /netsim/netsim_cfg > /dev/null 2>&1

ROOT_DIR=/netsim_users
CHROOT="no"

while getopts  "r:c" flag
do
    case "$flag" in
	r) ROOT_DIR="$OPTARG";;
	c) CHROOT="yes";;

	*) printf "Usage: %s <-r rootdir> -c <support chroot>\n" $0
           exit 1;;
    esac
done


for SIM in $LIST ; do
    SIM_NAME=`ls /netsim/netsimdir | grep -w ${SIM} | grep -v zip`
    if [ "${CHROOT}" = "no" ] ; then
	VOLUME="${ROOT_DIR}/${SIM}/%nename/c"
    else
	VOLUME="/c"
    fi

    ls ${ROOT_DIR}/${SIM} | egrep '^${SIM}$' > /dev/null
    if [ $? -eq 0 ] ; then
	cat - <<EOF
.selectnetype RNC
setmoattribute:mo="ManagedElement=1,SystemFunctions=1,PmService=1",attributes="performanceDataVolume (str)=${VOLUME}";
EOF
    fi

    ls ${ROOT_DIR}/${SIM} | egrep '^${SIM}RBS' > /dev/null
    if [ $? -eq 0 ] ; then
	cat - <<EOF
.selectnetype RBS
setmoattribute:mo="ManagedElement=1,SystemFunctions=1,PmService=1",attributes="performanceDataVolume (str)=${VOLUME}";
EOF
    fi

    ls ${ROOT_DIR}/${SIM} | egrep '^${SIM}RXI' > /dev/null
    if [ $? -eq 0 ] ; then
	cat - <<EOF
.selectnetype RXI
setmoattribute:mo="ManagedElement=1,SystemFunctions=1,PmService=1",attributes="performanceDataVolume (str)=${VOLUME}";
EOF
    fi

    ls ${ROOT_DIR}/${SIM} | egrep '^${SIM}ERBS' > /dev/null
    if [ $? -eq 0 ] ; then
	cat - <<EOF
.selectnetype ERBS
setmoattribute:mo="ManagedElement=1,SystemFunctions=1,PmService=1",attributes="performanceDataVolume (str)=${VOLUME}";
EOF
    fi

    ls ${ROOT_DIR}/${SIM} | egrep '^${SIM}PRBS' > /dev/null
    if [ $? -eq 0 ] ; then
	cat - <<EOF
.selectnetype PRBS
setmoattribute:mo="ComTop:ManagedElement=RNC109PRBS112,ComTop:SystemFunctions=1,ECIM_PM:Pm=1,ECIM_PM:PmMeasurementCapabilities=1",attributes="fileLocation (str)=${VOLUME}/pm_data";
EOF
    fi
done


