#!/bin/bash

utc_epoch=$(date +%s)
start_epoch=$(($((${utc_epoch}/300))*300))
current_offset=$(date -d @${start_epoch} +'%z')
OFFSET_TYPE=$(echo ${current_offset} | cut -c 1)
OFFSET_HOUR=$(echo ${current_offset} | cut -c 2,3)
OFFSET_MIN=$(echo ${current_offset} | cut -c 4,5)
hours=$(echo $(($OFFSET_HOUR*3600)))
minutes=$(echo $(($OFFSET_MIN*60)))
total=$(echo $(($hours + $minutes)))
if [[ ${OFFSET_TYPE} == "+" ]];then
    local_epoch=$(echo $(($start_epoch+$total)))
else
    local_epoch=$(echo $(($start_epoch-$total)))
fi
#FLEXROP_5_PLAYBACK_LOCAL="EPG-OI"
FLEX_ROP_CFG='/netsim_users/pms/etc/flex_rop_cfg'
if [ -r ${FLEX_ROP_CFG} ] ; then
   while IFS= read -r line
   do
     t=$line
     echo ${t} | grep '#!/bin/bash' > /dev/null
     if [ $? -ne 0 ] ; then
        rop=$(echo ${t} | awk -F'_' '{print $2}')
        scripttype=$(echo ${t} | awk -F'_' '{print $3}')
        timezone=$(echo ${t} | awk -F'_' '{print $4}' | cut -d '=' -f1)
        if [ $scripttype == 'GENSTATS' ];then
           nodelist=$(echo ${t} | awk -F'=' '{print $2}')
           script='/netsim_users/pms/bin/genStats'
           logfile='/netsim_users/pms/logs/genStats_'${rop}'min.log'
           nodelist=${nodelist/'RNC'/'RNC WRAN'}
           nodelist=${nodelist/'BSC'/'BSC MSC_BSC'}
        else
           script='/netsim_users/pms/bin/startPlaybacker.sh'
           logfile='/netsim_users/pms/logs/playbacker_'${rop}'min.log'
           nodelist=$(echo ${t} | awk -F'"' '{print $2}')
        fi
        if [ $timezone == 'LOCAL' ];then
           epoch=$local_epoch
        else
           epoch=$start_epoch
        fi
        remainder=$((epoch%(rop*60)))
        if [ $remainder -eq 0 ];then
           $script -r $rop -l "$nodelist" >> $logfile 2>&1
        fi
     fi
   done < "${FLEX_ROP_CFG}"
fi
