#!/bin/bash

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`

. ${BIN_DIR}/functions

. /netsim/netsim_cfg > /dev/null 2>&1

ROOT_DIR=/netsim_users
PMDIR="/c/pm_data"
while getopts  "p:r:" flag
do
    case "$flag" in

	p) PMDIR="$OPTARG";;
	r) ROOT_DIR="$OPTARG";;
	*) printf "Usage: %s < -p pmdir > <-r rootdir>\n" $0
           exit 1;;
    esac
done

for SIM in $LIST ; do
    echo "INFO: Configuring ${SIM}"
    SIM_ROOT_DIR=${ROOT_DIR}/${SIM}
    if [ ! -d ${SIM_ROOT_DIR} ] ; then
	mkdir -p ${SIM_ROOT_DIR}
	if [ $? -ne 0 ] ; then
	    echo "ERROR: Failed to create ${SIM_ROOT_DIR}"
	    exit 1
	fi
    fi

    SIM_NAME=`ls /netsim/netsimdir | grep -w ${SIM} | grep -v zip`
    NODE_LIST=`ls /netsim/netsim_dbdir/simdir/netsim/netsimdir/${SIM_NAME}`
    for NODE in ${NODE_LIST} ; do	
	NODE_DIR=${SIM_ROOT_DIR}/${NODE}${PMDIR}
	if [ ! -d ${NODE_DIR} ] ; then
	    mkdir -p ${NODE_DIR}
	    if [ $? -ne 0 ] ; then
		echo "ERROR: Failed to create ${NODE_DIR}"
		exit 1
	    fi
	fi
    done
done

