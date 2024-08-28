#!/bin/bash  
# This is responsible to copy the latest limitbw script to the mentioned netsims and to add cronjob
# to generate netsim traffic report periodically (at 1 AM everyday)

while getopts  "s:" flag
do
    case "$flag" in

        s) SERVER_LIST="$OPTARG";;
        *) printf "Usage: %s <-s serverlist>\n" $0
           exit 1;;
    esac
done
if [  -z "${SERVER_LIST}" ] ; then
    printf "Usage: %s <-s serverlist>\n" $0
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

SOURCE="/net/atns120dm2cge0/PM_Data/scripts_new/bin/limitbw"

NETSIM_PMS_DIR=/netsim_users/pms

NETSIM_BIN_DIR=${NETSIM_PMS_DIR}/bin


for SERVER in $SERVERS ; do
    echo "-------------------------"
    echo "Netsim : ${SERVER}"

   #rsh -l root ${SERVER} "if [ ! -d  ${NETSIM_BIN_DIR} ] ; then mkdir -p ${NETSIM_BIN_DIR} ;chown -R netsim:netsim ${NETSIM_PMS_DIR}; chmod 755 -R ${NETSIM_PMS_DIR} ; fi"
   echo shroot | su root -c "if [ ! -d  ${NETSIM_BIN_DIR} ] ; then mkdir -p ${NETSIM_BIN_DIR} ;chown -R netsim:netsim ${NETSIM_PMS_DIR}; chmod 755 -R ${NETSIM_PMS_DIR} ; fi"
   
   echo "Coping limitbw script"
   rcp ${SOURCE} root@${SERVER}:${NETSIM_BIN_DIR}
   #rsh -l root ${SERVER} "chown netsim:netsim ${NETSIM_BIN_DIR}/limitbw; chmod 755 ${NETSIM_BIN_DIR}/limitbw "
   echo shroot | su root -c "chown netsim:netsim ${NETSIM_BIN_DIR}/limitbw; chmod 755 ${NETSIM_BIN_DIR}/limitbw "

   echo "Add cron job to generate netsim traffic report"
   #rsh -l root ${SERVER} "crontab -l | egrep -v '^# |limitbw' > /tmp/new_crontab"
   echo shroot | su root -c "crontab -l | egrep -v '^# |limitbw' > /tmp/new_crontab"
   
   #rsh -l root ${SERVER} "echo \"0 * * * * ${NETSIM_BIN_DIR}/limitbw -n -g \" >> /tmp/new_crontab"
   echo shroot | su root -c "echo \"0 * * * * ${NETSIM_BIN_DIR}/limitbw -n -g \" >> /tmp/new_crontab"
   
   #rsh -l root ${SERVER} "crontab /tmp/new_crontab"
   echo shroot | su root -c "crontab /tmp/new_crontab"
   echo "------------------------"

done


