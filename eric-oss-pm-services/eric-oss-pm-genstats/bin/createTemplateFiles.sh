#!/bin/bash
#createTemplateFiles.sh
#######################################################################
#
#
#This script runs on the OSS Master server and loops through each of the mom files for wran,lte and core (DSC as of now) and creates
#a ROP template file. A config file is required for each MOM.
#These templates are then used by genStats to create the ROP files on the netsim boxes
#
#The xmlgen config files and the templates need to be updated/regenerated if a new MOM is 
#released or MOM versions change on OSS or new Motypes are added for CPP Nodes and new Node version of ECIM nodes
#we need counters for or if Number of cells, utran relations or gsmrelations that we want 
#to allocate counters for changes in the RNCs 
#
######################################################################


BIN_DIR=`dirname $0`
BIN_DIR=`cd ${BIN_DIR} ; pwd`
. ${BIN_DIR}/functions



while getopts  "c:t:g:" flag
do
    case "$flag" in	
	c) PMCONFIGPATH="$OPTARG";;
	t) PMTEMPLATEPATH="$OPTARG";;
	g) CONFIGFILE="$OPTARG";;
	*) printf "Usage: %s < -c config path > <-t template path> <-g configuration file>\n" $0
           exit 1;;
    esac
done

if [ -z "${PMCONFIGPATH}" ] || [ ! -d "${PMCONFIGPATH}" ] ; then
    echo "ERROR: You must specify the path containing the cfg files"
	printf "Usage: %s < -c config path > <-t template path> <-g configuration file>\n" $0
    exit 1
fi

if [ -z "${PMTEMPLATEPATH}" ] || [ ! -d "${PMTEMPLATEPATH}" ] ; then
    echo "ERROR: You must specify the path where to put the template files"
	printf "Usage: %s < -c config path > <-t template path> <-g configuration file>\n" $0
    exit 1
fi

if [ -z "${CONFIGFILE}" ] || [ ! -r ${CONFIGFILE} ] ; then
    log "ERROR: You have not specified the config file or cannot find config file : ${CONFIGFILE}"
	printf "Usage: %s < -c config path > <-t template path> <-g configuration file>\n" $0
    exit 1
fi

. ${CONFIGFILE} > /dev/null 2>&1


# STATS_WORKLOAD_LIST variable is must as this defines the rop configuration if not present then log
# message and exit the program execution.
if [ -z "${STATS_WORKLOAD_LIST}" ] ; then
    log "Variable STATS_WORKLOAD_LIST not found or not set in config file hence templates cannot be generated"
    exit 1
fi



MOMDIR=/opt/ericsson/nms_umts_wranmom/dat
NUM_OF_RNC_TYPES=7

log "Get MIB list"
/opt/ERICddc/util/bin/mibutil -list all > /tmp/miblist.txt 
log "Get Node list"
/opt/ERICddc/util/bin/listme > /tmp/listme.txt

MODEL_VERSION_LIST=`cat /tmp/listme.txt | grep '@2@3' | awk -F@ '{printf "%s:%s\n", $8, $3}' | sort -u`

for MODEL_VERSION in ${MODEL_VERSION_LIST} ; do
    MODEL=`echo ${MODEL_VERSION} | awk -F: '{print $1}'`
    NE_VERSION=`echo ${MODEL_VERSION} | awk -F: '{print $2}'`
    NODE_TYPE=`echo ${MODEL} | sed 's/_NODE_MODEL//'`

    if [ "${NODE_TYPE}" != "RNC" ] && [ "${NODE_TYPE}" != "RBS" ] && 
	[ "${NODE_TYPE}" != "RANAG" ] && [ "${NODE_TYPE}" != "ERBS" ] ; then
	continue;
    fi

	NODE=`cat /tmp/listme.txt | grep '@2@3@' | grep ${MODEL} | grep ${NE_VERSION} | head -1 | awk -F@ '{print $1}'`
	OSS_MIB_VER=`egrep ":${NODE}\$" /tmp/miblist.txt  | awk -F: '{print $2}'`
	OSS_MIB_VER_UN=`echo "${OSS_MIB_VER}" | sed 's/\./_/g'`
	MOMFILE=/opt/ericsson/nms_umts_wranmom/dat/${MODEL}_v${OSS_MIB_VER_UN}.xml
	log "Processing ${MODEL} ${NE_VERSION} ${OSS_MIB_VER}"
	NE_VERSION_UN=`echo ${NE_VERSION} | sed 's/^v//' | sed 's/\./_/g'`
   OPTS_ARGS=""

	
	ROP_LIST=`getStatsRopIntervalSupportedForNodeType ${NODE_TYPE}`
	for ROP in ${ROP_LIST} ; do
		
		PMCONFIGDIR=${PMCONFIGPATH}/${ROP}
		PMTEMPLATEDIR=${PMTEMPLATEPATH}/${ROP}
			if [ ${NODE_TYPE} = "RNC" ] ; then
				TYPE_INDEX=1
				TYPES_MATCHED=0
				while [ ${TYPE_INDEX} -le ${NUM_OF_RNC_TYPES} ] ; do
					OUT_FILE_BASE=TYPE_${TYPE_INDEX}_${NODE_TYPE}_${NE_VERSION_UN}		
					CFG_FILE=${PMCONFIGDIR}/TYPE_${TYPE_INDEX}_${NODE_TYPE}_${NE_VERSION_UN}.cfg
					OPTS_FILE=${PMCONFIGDIR}/TYPE_${TYPE_INDEX}_${NODE_TYPE}_${NE_VERSION_UN}.opts	    
					if [ -r ${CFG_FILE} ]; then		    		
							log " Generating for ${OUT_FILE_BASE}"
							if [ -r ${OPTS_FILE} ] ; then
								OPTS_ARGS="-opts ${OPTS_FILE}"
							fi
							${BIN_DIR}/cppXmlgen -mom ${MOMFILE} -cfg ${CFG_FILE} \
								-out ${PMTEMPLATEDIR}/${OUT_FILE_BASE}.template \
								-prop ${PMTEMPLATEDIR}/${OUT_FILE_BASE}.cntrprop  ${OPTS_ARGS} \
								> ${PMTEMPLATEDIR}/${OUT_FILE_BASE}.log

							TYPES_MATCHED=`expr ${TYPES_MATCHED} + 1`
					fi
					TYPE_INDEX=`expr ${TYPE_INDEX} + 1`
				done
				
				if [ ${TYPES_MATCHED} -eq 0 ] ; then
					log "ERROR: Cannot find any cfg file for RNC with MIM Version : ${NE_VERSION_UN} for ROP interval : ${ROP}"
					exit 1
				fi
			else
				FILE_BASE=${NODE_TYPE}_${NE_VERSION_UN}
				CFG_FILE=${PMCONFIGDIR}/${FILE_BASE}.cfg
					OPTS_FILE=${PMCONFIGDIR}/${FILE_BASE}.opts	    
				if [ ! -r ${CFG_FILE} ]; then		    
					log "ERROR: Cannot find ${CFG_FILE}"
					exit 1
				fi

				if [ -r ${OPTS_FILE} ] ; then
					OPTS_ARGS="-opts ${OPTS_FILE}"
				fi
				
				${BIN_DIR}/cppXmlgen -mom ${MOMFILE} -cfg ${CFG_FILE} \
					-out ${PMTEMPLATEDIR}/${FILE_BASE}.template \
					-prop ${PMTEMPLATEDIR}/${FILE_BASE}.cntrprop ${OPTS_ARGS} \
					> ${PMTEMPLATEDIR}/${FILE_BASE}.log
			fi
	done		
done

# ECIM Nodes types supported by PMS
ECIM_NE_TYPES="PRBS DSC MSRBS_V1 SAPC SGSN_MME MSRBS_V2"

#-mode t -inCfg H://TESTING//PRBS_13A.cfg -neType PRBS -neVer 13B -outFile H://TESTING//PRBS_13A.template -inRelFile C://MOM//EPIC_WCDMA_MOM_v9_0.xml -prop H://TESTING//PRBS_13A.cntrprop
for NE_TYPE in ${ECIM_NE_TYPES} ; do
    
	# Check the Node version list for the ECIM Node
	NE_VER_LIST=`/opt/ericsson/nms_cif_cs/etc/unsupported/bin/cstest -s Seg_masterservice_CS -ns masterservice lt ManagedElement -an mirrorRelease -f managedElementType==${NE_TYPE} | awk -F"\"" '{print $2 }' | sort -u`

	ROP_LIST=`getStatsRopIntervalSupportedForNodeType ${NE_TYPE}`
	for ROP in ${ROP_LIST} ; do
	    
	    PMCONFIGDIR=${PMCONFIGPATH}/${ROP}
		PMTEMPLATEDIR=${PMTEMPLATEPATH}/${ROP}
		
		for NE_VER in ${NE_VER_LIST} ; do

                      	FILE_BASE=${NE_TYPE}_${NE_VER} 
                      

			CFG_FILE="${PMCONFIGDIR}/${FILE_BASE}.cfg"
			
			if [ ! -r ${CFG_FILE} ]; then		    
					log "ERROR: Cannot find ${CFG_FILE}"
					exit 1
			fi
			
			# Generate template only as counter property file is not used by genStats script as of now.
			${BIN_DIR}/ecimXmlgen -mode t -neType ${NE_TYPE} -neVer ${NE_VER} -inCfg ${CFG_FILE} \
			-outFile ${PMTEMPLATEDIR}/${FILE_BASE}.template \
			> ${PMTEMPLATEDIR}/${FILE_BASE}.log
			
		done
	done 
done

log "templates stored in ${PMTEMPLATEPATH}"


#  ./createTemplateFiles.sh -c /net/atns120dm2cge0/PM_Data/deployment/atrcxb2651/O14A/xml_cfg -t /net/atns120dm2cge0/PM_Data/deployment/atrcxb2651/O14A/xml_templates -g /net/atrclin3/var/www/html/scripts/automation_wran/config/atrcxb2649-2651-50K-14A-WRAN.cfg


