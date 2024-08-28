#!/bin/bash
#
#setPmMeasurementCapabilityAttr.sh

#This script can used to set the fileLocation/jobStartStopSupport/measurementJobSupport attributes of MO PmMeasurementCapabilities
#
#XSURJAJ
#03-Sep-2014
#
#



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





SIM_LIST=`ls /netsim/netsimdir | grep "${SIM_NAME}" | grep -v zip`

for SIM in ${SIM_LIST} ; do
echo $SIM
        /netsim/inst/netsim_pipe <<EOF
.open ${SIM}
.selectnetype ${NE_TYPE}
.start
setmoattribute:mo="1", attributes="managedElementId=%NENAME%";
setmoattribute:mo="${MO_ID}", attributes="fileLocation=/c/pm_data/";
setmoattribute:mo="${MO_ID}", attributes="jobStartStopSupport=1";
setmoattribute:mo="${MO_ID}", attributes="measurementJobSupport=true";
.stop
.start -parallel
EOF

done
#./setFileLocationAttrForEcim.sh -s  TCU03  -t TCU03   -i  14


