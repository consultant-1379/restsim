#!/bin/bash


source ./functions > /dev/null 2>&1

PORT_IN_USE=`lsof -i:4545`
ON_DEMAND=`cat /netsim/netsim_cfg | grep ON_DEMAND | awk -F'=' '{print $2}' | tr -d '"'`

if [[ -z ${PORT_IN_USE} ]]; then
    log "INFO" "Starting server..." 
    python -u /netsim_users/pms/bin/Request_Listener/request_listener_controller.py >> /netsim_users/pms/logs/server.log & 
    sleep 1
    log "INFO" "Started in background."
else
    log "INFO" "Process already in use, check existing processes."
fi

process=`ps -aef | grep fileMetadataGenerator | grep -v "grep"`

if [[ $? -ne 0 ]]; then
    if [[ ${ON_DEMAND} == "true" ]]; then
        python -u /netsim_users/pms/bin/fileMetadataGenerator.py --mode on_demand >> /netsim_users/pms/logs/fileMetadata.log &
    else
        python -u /netsim_users/pms/bin/fileMetadataGenerator.py >> /netsim_users/pms/logs/fileMetadata.log &
    fi
fi

exit 0
