#!/bin/bash
#
#setFileLocationAttrForEcim.sh
#This script can used to set the fileLocation attribute of MO PmMeasurementCapabilities
#PMS reads value of this attribute as the remote path on ECIM node to search PM stats files for collection.
#
#XSURJAJ
#16-Sep-2013
#
#


SET_FILE_LOC_ATTR_COMMOND="setmoattribute:mo=MO_ID, attributes=\"fileLocation=/c/pm_data/\";"

while getopts  "s:t:i:" flag
do
    case "$flag" in
        s) SIM_NAME="$OPTARG";;
        t) NE_TYPE="$OPTARG";;
                i) MO_ID="$OPTARG";;


        *) printf "Usage: %s -s sim -t NE TYPE\n -i PmMeasurementCapabilities MO id\n" $0
            exit 1;;
    esac
done

if [ -z "${SIM_NAME}" -o -z "${NE_TYPE}" -o -z "${MO_ID}" ] ; then

            printf "Usage: %s -s sim -t NE TYPE\n -i PmMeasurementCapabilities MO id\n" $0
            exit 1

fi





SIM=`ls /netsim/netsimdir | grep "${SIM_NAME}" | grep -v zip`


        /netsim/inst/netsim_pipe <<EOF
.open ${SIM}
.selectnetype ${NE_TYPE}
setmoattribute:mo="${MO_ID}", attributes="fileLocation=/c/pm_data/";
.restart
EOF


#./setFileLocationAttrForEcim.sh -s  RNC108  -t PRBS   -n  28


