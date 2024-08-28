#!/bin/bash
source ./netsim_users/pms/bin/functions > /dev/null 2>&1

if [[ $ON_DEMAND == "false" ]]; then
    log "INFO : No need to cleanup request_listener" >> /tmp/setup.log
else
    crontab -l | grep -v request_listener > /tmp/_cron
    crontab /tmp/_cron
    log "INFO : Fetching PID of request listener server" >> /tmp/setup.log
    pid=`ps -aef | grep request_listener_controller | grep -v "grep" | awk -F' ' '{print $2}'`
    log "INFO : Terminating request listener process: $pid" >> /tmp/setup.log
    if [[ ! -z $pid ]]; then
        kill -9 $pid
    fi
    log "INFO : Finished" >> /tmp/setup.log
fi

