#!/bin/bash


# This script is responsible for rotating the logs

logs_path="/netsim_users/pms/logs/"
log_file="/netsim_users/pms/logs/log_rotation.log"

# This command greps ths respective log file and renames it as a backup file.
# In the next execution current logs will be renamed as backup ones and previous backup files forcefully overridden(removed)

echo "start time : `date`" >> $log_file

find $logs_path -type f \( -name '*min.log' -o -name '*rec.log' -o -name 'limitbw.log' -o -name '*service*.log' -o -name 'scanners.log' -o -name 'rmFiles.log' -o -name 'sim_pm_path.log' -o -name 'minilink_precook_data.log' \) -exec mv -f {} {}.bak \;

echo "end time : `date`" >> $log_file
