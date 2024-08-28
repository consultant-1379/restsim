#!/bin/bash


#add
    echo "*/15 * * * * /netsim_users/pms/bin/db_operation.sh -a >> /netsim_users/pms/logs/db_operations.log" >> /tmp/_cron
    echo "7 */2 * * * /netsim_users/pms/bin/db_operation.sh -d >> /netsim_users/pms/logs/db_operations.log" >> /tmp/_cron

    crontab /tmp/_cron
    rm -rf /tmp/_cron

#del
    cron -l | grep -v "db_operation" >> /tmp/_cron

    crontab /tmp/_cron
    rm -rf /tmp/_cron
