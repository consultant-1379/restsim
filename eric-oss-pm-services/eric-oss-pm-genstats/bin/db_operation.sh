#!/bin/bash

OP=""

while getopts  "adu" flag
do
    case "$flag" in
        a) OP="-a";;
        d) OP="-d";;
        u) OP="-u";;
        *) printf "Usage: %s < -a Add files > < -d Del files >\n" $0
           exit 1;;
    esac
done


if [[ ${OP} = "-a" && -f /tmp/values.json ]]; then
    echo "`date` Adding files to db"
    java -jar /netsim_users/pms/lib/fls-updator-service.jar add '/tmp/values.json' 'eric-oss-fls-enm-id' 'FLS_PORT'
elif [[ ${OP} = "-d" && -f /tmp/rm.json ]]; then
    echo "`date` Deleting files from db"
    java -jar /netsim_users/pms/lib/fls-updator-service.jar delete '/tmp/rm.json' 'eric-oss-fls-enm-id' 'FLS_PORT'
    rm -rf /tmp/rm.json
elif [[ ${OP} = "-u" ]]; then
    echo "`date` Updating instrumentation data"
    java -jar /netsim_users/pms/lib/fls-updator-service.jar addInstrumentation '/tmp/instrument.json' 'eric-oss-fls-enm-id' 'FLS_PORT'
fi
