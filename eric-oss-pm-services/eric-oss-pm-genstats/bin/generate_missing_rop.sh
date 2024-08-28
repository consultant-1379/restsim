#!/bin/bash

missing_rop_epoch=$1

get_system_date(){
    echo `date`
}

echo "`get_system_date` : INFO : Calling PM generation with epoch ${missing_rop_epoch}" >> /tmp/setup.log
if [[ $CELLTRACE_ENABLED == "true" ]]; then
    /netsim_users/pms/bin/lte_rec.sh -r 15 -f CELLTRACE -j ${missing_rop_epoch} >> /netsim_users/pms/logs/lte_rec_15min.log &
fi
if [[ $STATS_ENABLED == "true" ]] || [[ $REPLAY_ENABLED == "true" ]]; then
    /netsim_users/pms/bin/genStats -r 15 -j ${missing_rop_epoch} >> /netsim_users/pms/logs/genStats_15min.log &
fi
if [[ $PLAYBACK_ENABLED == "true" ]]; then
    /netsim_users/pms/bin/startPlaybacker.sh -r 15 -j ${missing_rop_epoch} >> /netsim_users/pms/logs/playbacker_15min.log &
fi

