#!/bin/bash


get_system_date(){
    echo `date`
}

ln -s /usr/bin/python3.6 /usr/bin/python

echo "`get_system_date` : INFO : Initiating  setup on container..." >> /tmp/setup.log

setup_default() {
    sudo mkdir -p /netsim_users/pms/bin
    sudo mkdir -p /netsim_users/auto_deploy/bin
    sudo mkdir -p /netsim_users/hc/bin/
    sudo mkdir -p /netsim_users/pms/etc/
    sudo mkdir -p /netsim_users/pms/lib/
    sudo mkdir -p /netsim_users/pms/logs/
    sudo mkdir -p /netsim_users/pms/xml_templates/15/
    sudo mkdir -p /netsim_users/pms/xml_templates/1/
    sudo mkdir -p /netsim_users/pms/rec_templates/
    sudo mkdir -p /netsim/genstats/tmp/
    sudo mkdir -p /etc/config/
    sudo mkdir -p /recordings
    sudo mkdir -p /netsim_users/pms/config/touch_files/
    sudo mkdir -p /netsim_users/pms/config/json/
    sudo mkdir -p /netsim_users/pms/config/requests/
    sudo mkdir -p /netsim_users/pms/xml_templates/replay/DU
    sudo mkdir -p /netsim_users/pms/xml_templates/replay/CUUP
    sudo mkdir -p /netsim_users/pms/xml_templates/replay/CUCP
    sudo mkdir -p /netsim_users/pms/xml_templates/replay/ERBS
    sudo mkdir -p /netsim_users/pms/sandbox_templates/vDU
    sudo mkdir -p /netsim_users/pms/sandbox_templates/vCU-CP
    sudo mkdir -p /netsim_users/pms/sandbox_templates/vCU-UP
    sudo mkdir -p /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_AMF
    sudo mkdir -p /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_SMF
    sudo mkdir -p /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCG_UPF


    unzip /genstats_file.zip
    sudo mv /genstats_files/deployment/* /netsim_users/auto_deploy/bin
    sudo mv /genstats_files/config/showstartednodes.txt /tmp/
    sudo mv /genstats_files/bin/* /netsim_users/pms/bin
    sudo mv /genstats_files/config/nr_cell_data.txt /netsim_users/pms/etc/
    sudo mv /genstats_files/config/netsim_cfg /netsim/
    sudo mv /genstats_files/config/topology_config.ini /netsim_users/pms/etc/
    sudo mv /genstats_files/config/PCG_ESOA.cfg /netsim_users/pms/etc/
    sudo mv /genstats_files/config/PCC_ESOA.cfg /netsim_users/pms/etc/
    sudo mv /genstats_files/config/PCC_AMF_ESOA.cfg /netsim_users/pms/etc/

    sudo mv /genstats_files/hc/* /netsim_users/hc/bin/
    sudo mv /genstats_files/lib/genstats-jar-with-dependencies.jar /netsim_users/pms/lib/fls-updator-service.jar

    sudo mv /genstats_files/templates/PCC_node.xml.gz /netsim_users/pms/xml_templates/1/
    sudo mv /genstats_files/templates/PCG_node.xml.gz /netsim_users/pms/xml_templates/1/



    if [[ $REPLAY_ENABLED == "true" ]] && [[ $EBSN_PERFORMANCE_ENABLED == "true" ]]; then
            sudo mv /genstats_files/templates/EBSN_performance/*CUCP*.xml /netsim_users/pms/xml_templates/replay/CUCP
            sudo mv /genstats_files/templates/EBSN_performance/*DU*.xml /netsim_users/pms/xml_templates/replay/DU
    else
            sudo mv /genstats_files/templates/*DU*.xml /netsim_users/pms/xml_templates/replay/DU
      sudo mv /genstats_files/templates/*CUUP*.xml /netsim_users/pms/xml_templates/replay/CUUP
      sudo mv /genstats_files/templates/*CUCP*.xml /netsim_users/pms/xml_templates/replay/CUCP
    fi

    if [[ ${PCC_PCG_FOR_ESOA} == "true" ]] && [[ ${PCC_PCG_FOR_ESOA_PERFORMANCE} == "true" ]]; then
      # Moving Performance templates
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_templates/PCC_AMF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_AMF
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_templates/PCC_SMF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_SMF
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_templates/PCG_UPF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCG_UPF
    else
      # Moving Functional templates
      # Need to create new folder PCC_PCG_ESOA_Functional_templates
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_functional_templates/PCC_AMF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_AMF
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_functional_templates/PCC_SMF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCC_SMF
      sudo mv /genstats_files/templates/PCC_PCG_ESOA_functional_templates/PCG_UPF/* /netsim_users/pms/xml_templates/PCC_PCG_ESOA/PCG_UPF
    fi

    sudo mv /genstats_files/templates/CNF_vDU.xml.gz /netsim_users/pms/sandbox_templates/vDU
    sudo mv /genstats_files/templates/CNF_vCU-CP.xml.gz /netsim_users/pms/sandbox_templates/vCU-CP
    sudo mv /genstats_files/templates/CNF_vCU-UP.xml.gz /netsim_users/pms/sandbox_templates/vCU-UP
    sudo mv /genstats_files/templates/*LRAN*.xml /netsim_users/pms/xml_templates/replay/ERBS

    sudo mv /genstats_files/config/* /netsim_users/pms/etc/

    sudo cp /recording_files-23.10.1.zip /recordings
    sudo cp /netsim_users/pms/xml_templates/1/* /netsim_users/pms/xml_templates/15/
    sudo cp /etc/config-map/config.json /etc/config/config.json

    sudo unzip /recordings/recording_files-23.10.1.zip -d /recordings/
    sudo cp /genstats_files/templates/lte_* /netsim_users/pms/xml_templates/15/
    sudo cp /recordings/recording_files_NRM3/* /netsim_users/pms/rec_templates/

    sudo chmod -R 777 /netsim_users/

    ENM=`echo ${POD_ENM_ID//-/_} | awk -F"_" '{printf "%s_%s", $5, $6}'`
    ENM_ID=`echo $ENM | awk -F"_" '{print $2}'`
    env | grep ENABLED >> /netsim/netsim_cfg
    sed -i "s/ENM_ID=\"\"/ENM_ID=\"$ENM\"/g" /netsim/netsim_cfg
    sed -i "s/ON_DEMAND=\"\"/ON_DEMAND=\"${ON_DEMAND}\"/g" /netsim/netsim_cfg
    sed -i "s/EBSN_REPLAY_COUNTER_MAPPING=\"\"/EBSN_REPLAY_COUNTER_MAPPING=\"${EBSN_REPLAY_COUNTER_MAPPING}\"/g" /netsim/netsim_cfg
    sed -i "s/PCC_PCG_FOR_ESOA=\"\"/PCC_PCG_FOR_ESOA=\"${PCC_PCG_FOR_ESOA}\"/g" /netsim/netsim_cfg
    sed -i "s/PCC_PCG_FOR_ESOA_PERFORMANCE=\"\"/PCC_PCG_FOR_ESOA_PERFORMANCE=\"${PCC_PCG_FOR_ESOA_PERFORMANCE}\"/g" /netsim/netsim_cfg

    if [[ $REPLAY_ENABLED == "false" ]]; then
        sed -i "s/ENABLED_STATIC_REPLAY=/#ENABLED_STATIC_REPLAY=/g" /netsim/netsim_cfg
    fi
    sed -i "s/LARGE_SCALE=/LARGE_SCALE=\"${LARGE_SCALE}\"/g" /netsim/netsim_cfg
    sed -i "s/STATS_MAX_CONCURRENT=4/STATS_MAX_CONCURRENT=${CONCURRENCY}/g" /netsim/netsim_cfg
    python /netsim_users/pms/bin/setup_container_nodes.py -g deploy_config >> /tmp/setup_container.log

    NR_NODES=`cat /etc/config/config.json  | grep NR_NES_PER_SIM | awk -F':' '{print $2}' | tr -d '," '`
    LTE_NODES=`cat /etc/config/config.json | grep DG2_NES_PER_SIM | awk -F':' '{print $2}' | tr -d '," '`

    for cell in `echo "1 3 6 12"`; do
        sudo cp /genstats_files/templates/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x40-gNodeBRadio-NRAT-NR192_${cell}CELLS.xml /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x${NR_NODES}-gNodeBRadio-NRAT-NR01_${cell}CELLS.xml
        sudo cp /genstats_files/templates/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x40-gNodeBRadio-NRAT-NR192_${cell}CELLS.cntrprop /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x${NR_NODES}-gNodeBRadio-NRAT-NR01_${cell}CELLS.cntrprop
    done

    file_types="xml cntrprop"

    for type in $file_types; do
        for sim in `cat /netsim/genstats/tmp/sim_data.txt | grep "NR" | awk -F':' '{print $2}' | awk -F' ' '{print $1}'`; do
            for cp_cell in `echo "1 3 6 12"`; do
                echo " /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x${NR_NODES}-gNodeBRadio-NRAT-NR01_${cp_cell}CELLS.${type}  /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_${sim}_${cp_cell}CELLS.${type}"
                cp -u /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_NR21-Q4-V1x${NR_NODES}-gNodeBRadio-NRAT-NR01_${cp_cell}CELLS.${type} /netsim_users/pms/xml_templates/15/gnodebradio_counters_21-Q4-V1_${sim}_${cp_cell}CELLS.${type}
            done
        done
    done
    sed -i -e "s/-id/-${ENM_ID}/g" -e "s/FLS_PORT/8080/g" /netsim_users/pms/bin/crud_operator.py
    PM_DIR_LIST=""
    if [[ $STATS_ENABLED == "true" ]];then
        PM_DIR_LIST="$PM_DIR_LIST STATS"
    fi
    if [[ $CELLTRACE_ENABLED == "true" ]];then
        PM_DIR_LIST="$PM_DIR_LIST CELLTRACE"
    fi
    if [[ $REPLAY_ENABLED == "true" ]];then
        PM_DIR_LIST="$PM_DIR_LIST REPLAY"
    fi
    if [[ $FUTURE_ENABLED == "true" ]];then
        PM_DIR_LIST="$PM_DIR_LIST FUTURE"
    fi

    echo "PM_DIR_LIST=\"$PM_DIR_LIST\"" >> /netsim/netsim_cfg

    OLD_LIST=$LIST

    for sim in `cat /netsim/genstats/tmp/sim_data.txt | awk -F':' '{print $2}' | awk -F' ' '{print $1}'`; do
        sudo mkdir -p /netsim/netsim_dbdir/simdir/netsim/netsimdir/${sim}/
    done

    if [[ $STATS_ENABLED == "true" ]] || [[ $REPLAY_ENABLED == "true" ]]; then
        echo "*/15 * * * * /netsim_users/pms/bin/genStats -r 15 >> /netsim_users/pms/logs/genStats_15min.log" >> /tmp/_cron
    fi
    if [[ $PLAYBACK_ENABLED == "true" ]]; then
        echo "*/15 * * * * /netsim_users/pms/bin/startPlaybacker.sh -r 15 >> /netsim_users/pms/logs/playbacker_15min.log" >> /tmp/_cron
    fi
    echo "0 * * * * /netsim_users/pms/bin/rmPmFiles >> /netsim_users/pms/logs/rmFiles.log" >> /tmp/_cron
    #echo "12-59/15 * * * * python /netsim_users/pms/bin/setup_container_nodes.py -g scale_config" >> /tmp/_cron
    echo "* * * * * /netsim_users/pms/bin/initiate_listener_service.sh > /dev/null 2>&1" >> /tmp/_cron

    if [[ $CELLTRACE_ENABLED == "true" ]]; then
        echo "*/15 * * * * /netsim_users/pms/bin/lte_rec.sh -r 15 -f CELLTRACE >> /netsim_users/pms/logs/lte_rec_15min.log" >> /tmp/_cron
    fi

    echo "`get_system_date` : INFO :  Taking system epoch time..." >> /tmp/setup.log

    current_epoch=$(date +%s)
    # 11:31:00, 11:38:00, 11:41:00, 11:44:56, 11:45:00

    let "mod_sys_time=current_epoch%900"

    if [[ ${mod_sys_time} -eq 0 ]]; then
        sleep 5
        current_epoch=$(date +%s)
    fi

    echo "`get_system_date` : INFO : System epoch time taken : ${current_epoch}." >> /tmp/setup.log

    let "c_epoch_round_off=current_epoch/900"
    let "c_epoch_round_off=c_epoch_round_off*900"
    echo "`get_system_date` : INFO : System round off epoch time : ${c_epoch_round_off}." >> /tmp/setup.log
    # 11:30:00, 11:30:00, 11:30:00, 11:30:00, 11:45:00

    let "next_epoch=c_epoch_round_off+900"
    echo "`get_system_date` : INFO : System next rop round off epoch time : ${next_epoch}." >> /tmp/setup.log
    # 11:45:00, 11:45:00, 11:45:00, 11:45:00, 12:00:00

    let "time_before_next_rop=next_epoch-current_epoch"
    # 14 min, 7 min, 4 min, > 0 min, > 14 min

    if [[ ${time_before_next_rop} -gt 599 ]]; then
        # We have 10 minutes or more time to generate PM, so setting up cron and calling PM generation.
        echo "`get_system_date` : INFO : Setting up crons.." >> /tmp/setup.log
        crontab /tmp/_cron
        echo "`get_system_date` : INFO : Cron setup successful." >> /tmp/setup.log

        echo "`get_system_date` : INFO : Calling PM generation with current epoch ${c_epoch_round_off}" >> /tmp/setup.log
        if [[ $CELLTRACE_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/lte_rec.sh -r 15 -f CELLTRACE -j ${c_epoch_round_off} >> /netsim_users/pms/logs/lte_rec_15min.log &
        fi
        if [[ $STATS_ENABLED == "true" ]] || [[ $REPLAY_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/genStats -r 15 -j ${c_epoch_round_off} >> /netsim_users/pms/logs/genStats_15min.log &
        fi
        if [[ $PLAYBACK_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/startPlaybacker.sh -r 15 -j ${c_epoch_round_off} >> /netsim_users/pms/logs/playbacker_15min.log &
        fi
        wait
    else
        echo "`get_system_date` : INFO : Calling PM generation with current epoch ${c_epoch_round_off}" >> /tmp/setup.log
        if [[ $CELLTRACE_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/lte_rec.sh -r 15 -f CELLTRACE -j ${c_epoch_round_off} >> /netsim_users/pms/logs/lte_rec_15min.log &
        fi
        if [[ $STATS_ENABLED == "true" ]] || [[ $REPLAY_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/genStats -r 15 -j ${c_epoch_round_off} >> /netsim_users/pms/logs/genStats_15min.log &
        fi
        if [[ $PLAYBACK_ENABLED == "true" ]]; then
            /netsim_users/pms/bin/startPlaybacker.sh -r 15 -j ${c_epoch_round_off} >> /netsim_users/pms/logs/playbacker_15min.log &
        fi
        wait

        after_generation_epoch=$(date +%s)
        let "ten_seconds_before_next_rop=next_epoch-10"
        if [[ ${after_generation_epoch} -lt ${ten_seconds_before_next_rop} ]]; then
            echo "`get_system_date` : INFO : Setting up crons.." >> /tmp/setup.log
            crontab /tmp/_cron
            echo "`get_system_date` : INFO : Cron setup successful." >> /tmp/setup.log
        else
            sleep 15
            crontab /tmp/_cron
            /netsim_users/pms/bin/generate_missing_rop.sh ${next_epoch} > /dev/null 2>&1
        fi
    fi

    /netsim_users/pms/bin/initiate_listener_service.sh > /dev/null 2>&1
    echo "`get_system_date` : INFO : Setup complete" >> /tmp/setup.log
}

setup_static_replay() {

    mkdir -p /ericsson/pmic/XML/replay/
    unzip /genstats_file.zip
    mkdir -p /netsim_users/pms/bin/
    mkdir -p /netsim_users/pms/logs/
    sudo mv /genstats_files/bin/crud_operator.py /netsim_users/pms/bin
    sed -i -e "s/FLS_IP/${ERIC_OSS_FLS_SERVICE_HOST}/g" -e "s/FLS_PORT/${ERIC_OSS_FLS_SERVICE_PORT}/g" /netsim_users/pms/bin/crud_operator.py

    echo "16-59/15 * * * * python /netsim_users/pms/bin/json_populator.py --mode static >> /netsim_users/pms/logs/json.log" >> /tmp/_cron
    echo "*/15 * * * * /netsim_users/pms/bin/crud_operator.py -a DEFAULT >> /netsim_users/pms/logs/crud_operations.log" >> /tmp/_cron
    echo "7 */2 * * * /netsim_users/pms/bin/crud_operator.py -d '/tmp/rm.json'>> /netsim_users/pms/logs/crud_operations.log" >> /tmp/_cron

    crontab /tmp/_cron

}

if [[ $STATIC_PLAYBACK == "true" ]]; then
    setup_static_replay
else
    setup_default
fi

# Creates SFTP user and configures OpenSSH
/create_user.sh
