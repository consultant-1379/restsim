#!/bin/bash 

BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`

CONFIGFILE=/netsim/netsim_cfg
REPO="NEXUS"

while getopts  "s:c:r:" flag
do
    case "$flag" in
	
	c) CONFIGFILE="$OPTARG";;
	s) SERVER_LIST="$OPTARG";;
        r) REPO="$OPTARG";;
	*) printf "Usage: %s < -c configfile > <-s serverlist> [-r repo(NFS/NEXUS)]\n" $0
           exit 1;;
    esac
done
if [ ! -r ${CONFIGFILE} ] ; then
    echo "ERROR: Cannot find ${CONFIGFILE}"
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1
if [ ! -z "${SERVER_LIST}" ] ; then
    SERVERS="${SERVER_LIST}"
fi

for SERVER in $SERVERS ; do
    echo "INFO: ${SERVER}"

        if [ "${REPO}" = "NFS" ] ; then
		#/usr/bin/rsh -l root ${SERVER} "zypper addrepo --disable --check --refresh nfs://159.107.177.99/var/repo/systemtest/test st_test"
		echo shroot | su root -c "zypper addrepo --disable --check --refresh nfs://159.107.177.99/var/repo/systemtest/test st_test"
		
		#/usr/bin/rsh -l root ${SERVER} "zypper addrepo --check --refresh nfs://159.107.177.99/var/repo/systemtest/release st_release"
		echo shroot | su root -c "zypper addrepo --check --refresh nfs://159.107.177.99/var/repo/systemtest/release st_release"
		
		#/usr/bin/rsh -l root ${SERVER} "zypper --gpg-auto-import-keys  --non-interactive install ERICnetsimpmcpp_CXP9029065"
        echo shroot | su root -c "zypper --gpg-auto-import-keys  --non-interactive install ERICnetsimpmcpp_CXP9029065"
        
        else
		
		#/usr/bin/rsh -l root ${SERVER} "curl -L \"https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=releases&g=com.ericsson.cifwk.netsim&a=ERICnetsimpmcpp_CXP9029065&p=rpm&v=RELEASE\" -o /tmp/ERICnetsimpmcpp_CXP9029065.rpm"
		echo shroot | su root -c "curl -L \"https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=releases&g=com.ericsson.cifwk.netsim&a=ERICnetsimpmcpp_CXP9029065&p=rpm&v=RELEASE\" -o /tmp/ERICnetsimpmcpp_CXP9029065.rpm"
		
		#/usr/bin/rsh -l root ${SERVER} rpm -ivh --force /tmp/ERICnetsimpmcpp_CXP9029065.rpm
		echo shroot | su root -c "rpm -ivh --force /tmp/ERICnetsimpmcpp_CXP9029065.rpm"
		
		#/usr/bin/rsh -l root ${SERVER} rm /tmp/ERICnetsimpmcpp_CXP9029065.rpm
		echo shroot | su root -c "rm -f /tmp/ERICnetsimpmcpp_CXP9029065.rpm"
		
        fi
done

