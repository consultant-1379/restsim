#!/bin/bash
# Created by  : Fatih ONUR
# Created on  : 2016.04.10
# File name   : set_tmpfs.sh

function usage_msg() {
cat << EOF
Help:
    Sets tmpfs filesystem for LTE|MGW|SPITFIRE|TCU|RNC|UPG|WCG|WMG|DSC|VRC|VPP|RNNODE|VRM|VRSM|VSAPC simulations on /pms_tmpfs mount point

Usage:
   $0 <sim_name> [<force>]

    where:
       <sim_name>: specifies simulation name
       [<force>]: optional. specifies forcefully set tmpfs arg. Accepted values: yes/no

    usage examples:
       $0 LTEG1124-limx160-5K-FDD-LTE03
       $0 LTEG1124-limx160-5K-FDD-LTE03 yes

    dependencies:
        1. Should /pms_tmpfs mount point exist before.

    Return Values:
        1 -> Sims are set with tmpfs
        2 -> Usage is incorrect
EOF
}

# Params
SIM=$1
FORCE=$2


# Generic env vars
PWD=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ARGS=$#


# Specific env vars
SCRIPT_NAME=$(basename "$0")
LOGFILE=/tmp/$SCRIPT_NAME.log
TMPFS_DIR=/pms_tmpfs
NETSIM_PIPE=/netsim/inst/netsim_pipe
NETSIM_DIR=/netsim/netsimdir
NODE_TYPES="lte mgw spitfire tcu rnc esapc epg mtas cscf sbg mrf vbgf ipworks hss-fe upg wcg wmg dsc vrc vpp rnnode fronthaul ml dsc dog c608 eme siu02 r6672 r6673 r6675 r6274 r6371 r6471-1 r6471-2 vrm vrsm ers_sn_esc ers_sn_scu ersn mrs scu_"

function check_args() {
    USAGE_SHOW=0
    if [[ ! -z "$SIM" ]] ; then
        #echo "DEBUG: zSIM:$SIM"
        if ! is_valid_sim $SIM; then
            echo "ERROR: Invalid sim:$SIM. Please verify your sim name" | tee -a $LOGFILE
            USAGE_SHOW=-1
        fi
    fi

    if [[ ! -z "$FORCE" ]] ; then
        FORCE=`echo $FORCE| awk '{print tolower($0)}'`
        #echo "DEBUG: FORCE:$FORCE:"
        case "$FORCE" in
           [yY] | yes )
               #echo "DEBUG: Selected value for FORCE:$FORCE"
            ;;
           [nN] | no )
               #echo "DEBUG: Selected value for FORCE:$FORCE"
            ;;
           * ) echo "ERROR: Invalid value for FORCE arg. Valid values:YES|NO" | tee -a $LOGFILE
               USAGE_SHOW=-1
            ;;
         esac
    else
        FORCE="no"
        #echo "DEBUG: default value for FORCE:$FORCE"
    fi

    if [[ $USAGE_SHOW -ne 0 ]]; then usage_msg; exit -1; fi
}


function is_valid_sim() {
    local SIM_NAME=$1
    local VALID_NUM=`ls $NETSIM_DIR | egrep -c "^${SIM_NAME}$"`
    #echo "DEBUG: VALID_NUM:$VALID_NUM"
    if [[ $VALID_NUM -gt 0 ]]; then
       #echo "DEBUG: VALID"
       return 0 # true
    else
       #echo "DEBUG: INVALID"
       return -1 # false
    fi
}

function get_sim() {
    local SIM_NAME=$1
    local SIM=`echo $SIM_NAME | perl -ne 'if (/lte/i || /rnc/i){/.*-(\S.*\d)/ && print $1}else{print}'`
    echo $SIM
}


function is_tmpfs_required() {
    local SIM_NAME=$1
    local SIM_NAME_LOWER=`echo $SIM_NAME | awk '{print tolower($0)}'`
    if [[ ${SIM_NAME_LOWER} =~ "lte" ]] ; then
        local SIM_ID=`echo $SIM_NAME | perl -ne 'if(/lte/i){/(\d+)$/; print $1+0 . "\n"}else{print}'`
        echo "DEBUG: SIM:$SIM"
        if [[ $SIM_ID -ge 126 ]] ; then
            return -1 # false
        fi
    fi
    return 0 # true
}


function is_tmpfs_set() {
    local SIM_NAME=$1
    local SIM=`get_sim $SIM_NAME`

    echo "INFO: SIM:$SIM" | tee -a $LOGFILE
    $NETSIM_PIPE <<EOF | tee /dev/tty | tee -a $LOGFILE | awk '{if ( $2 ~ /^fs$/ ) { NE = $1; } else if ( $1 ~ /^tmpfs$/ ) { printf "%s %s\n", NE, $2;} }' > /tmp/${SIM}_tmpfs.txt #2>&1 | tee -a $LOGFILE
.open ${SIM_NAME}
.selectnocallback network
.show fs
EOF

    TMPFS_NOT_SET_NUM=`cat /tmp/${SIM}_tmpfs.txt | egrep -cv ": ${TMPFS_DIR}/${SIM}/"`
    echo "INFO: TMPFS_NOT_SET_NUM=$TMPFS_NOT_SET_NUM" | tee -a $LOGFILE
    if [[ $TMPFS_NOT_SET_NUM -gt 0 ]] ; then
       return 0 # true
    else
       return -1 # false
    fi
}

function set_tmpfs() {
    local SIM_NAME=$1
    local SIM=`get_sim $SIM_NAME`
    echo " simname is $SIM_NAME "
    if [[ ${SIM_NAME} =~ "vRC" || ${SIM_NAME} =~ "vPP" || ${SIM_NAME} =~ "RNN" || ${SIM_NAME} =~ "vSD" || ${SIM_NAME} =~ "5GRadioNode" || ${SIM_NAME} =~ "VTFRadioNode" || ${SIM_NAME} =~ "vRM" || ${SIM_NAME} =~ "vRSM" || ${SIM_NAME} =~ "VSAPC" || ${SIM_NAME} =~ "VTIF" ]] ; then
        SIM=$SIM_NAME
        echo "sim is $SIM"
    fi
    if [[ "${SIM_NAME#*"ML"}" != "${SIM_NAME}" ]]; then
           $NETSIM_PIPE <<EOF | awk '/OK/{f=0;};f{print $1;};/NE Name/{f=1;}' > /tmp/${SIM_NAME}_tmpfs.txt
.open ${SIM_NAME}
.selectnocallback network
.show simnes
EOF
           rm -rf ${TMPFS_DIR}/${SIM_NAME}
           while read node_name
           do
                mkdir -p ${TMPFS_DIR}/${SIM_NAME}/${node_name}/c/pm_data/
           done < /tmp/${SIM_NAME}_tmpfs.txt
     fi
    $NETSIM_PIPE <<EOF | tee -a $LOGFILE
.open ${SIM_NAME}
.selectnocallback network
.stop
.set fs tmpfs ${TMPFS_DIR}/${SIM}/%nename force
.set save
.start -parallel 5
EOF
    # Remove file locations files if any created by netsim command 'set fs tmpfs'
    find ${TMPFS_DIR} \( -name 'UeTraceFilesLocation'  -o -name 'CellTraceFilesLocation' \) -exec rm {} \;
}

if [[ $ARGS -eq 0 || $ARGS -gt 2 ]] ; then
    echo "ERROR: Invalid arguments"
    usage_msg
    exit;
fi
check_args

echo "RUNNING: $0 $SIM $FORCE script started running at "`date` | tee $LOGFILE
echo "" | tee -a $LOGFILE

echo "INFO: NODE_TYPES:$NODE_TYPES" | tee -a $LOGFILE

if [ ! -d $TMPFS_DIR ] ; then
    echo "ERROR: First create $TMPFS_DIR mount point" | tee -a $LOGFILE
    exit 1;
fi

for NODE_TYPE in $NODE_TYPES; do
    SIM_FILTER=`echo ${SIM} | sed 's/-/_/g'`
    SIM_NAME=`echo ${SIM_FILTER} | awk '{print tolower($0)}'`
    if [[ ${SIM_NAME} =~ $NODE_TYPE ]] ; then
        echo "INFO: NODE_TYPE:$NODE_TYPE, SIM:$SIM" | tee -a $LOGFILE
        if [[ "$FORCE" = "yes" ]] ; then
            set_tmpfs $SIM
        else
            if is_tmpfs_required $SIM ; then
                set_tmpfs $SIM
            else
                echo "INFO: No set tmpfs requried for sim:$SIM" | tee -a $LOGFILE
            fi
        fi
        break
    fi
done

echo "" | tee -a $LOGFILE
echo "...$0 script $SIM $FORCE ended at "`date` | tee -a $LOGFILE
echo "" | tee -a $LOGFILE

