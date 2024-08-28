#!/bin/bash

CONF_FILE="/netsim_users/reference_files/config.ini"

RETENTION_TIME=""
DATA_LOCATION=""

if [[ -f "${CONF_FILE}" ]]; then
	RETENTION_TIME=$(cat ${CONF_FILE} | grep -w 'DATA_RETENTION_PERIOD_HOUR' | awk -F'=' '{print $2}' | sed 's/ //g')
	if [[ ! -z "${RETENTION_TIME}" ]]; then
	    RETENTION_TIME=$((${RETENTION_TIME}*60))
	else
	    RETENTION_TIME="1440"
	fi
	
	DATA_LOCATION=$(cat ${CONF_FILE} | grep -w 'DESTINATION_LOCATION' | awk -F'=' '{print $2}' | sed 's/ //g')
	if [[ ! -z "${DATA_LOCATION}" ]]; then
	    find ${DATA_LOCATION}/*/ -name '*.mss.*' -mmin +${RETENTION_TIME} -exec rm {} \;
	else
	    echo "ERROR: Output location not found in ${CONF_FILE} file."
	    exit 1
	fi
else
    echo "ERROR: ${CONF_FILE} file not present."
    exit 1
fi
