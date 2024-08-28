#!/usr/bin/python
################################################################################
# COPYRIGHT Ericsson 2018
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 21.12
# Purpose       :  Log genstats Instrumentation statistics
# Jira No       :  NSS-35742
# Gerrit Link   :
# Description   :  R6673 Models- Genstats
# Date          :  21/06/2021
# Last Modified :  tom.mcgreal@ericsson.com
####################################################


import os, logging
import re,sys,glob
from subprocess import Popen, PIPE
from GenericMethods import fetchNetsimCfgParam
from DataAndStringConstants import NETSIM_DBDIR
from itertools import chain
import json
import datetime

SHOW_STARTED_NODES = "/tmp/showstartednodes.txt"
NETSIM_CFG = "/netsim/netsim_cfg"
SIM_DATA_FILE = '/netsim/genstats/tmp/sim_data.txt'
TMPFS_DIR = '/pms_tmpfs/'
INSTRUMENTATION_DIR = '/netsim/genstats/logs/'
pm_data = "/c/pm_data/"
bsc_ready_path = "/apfs/data_transfer/destinations/CDHDEFAULT/Ready"
msc_ready_path = "/apfs/data_transfer/destinations/CDHDEFAULT/Ready"
tsp_opt_path = "/opt/telorb/axe/tsp/NM/PMF/reporterLogs"
hlr_ready_path = "/data_transfer/destinations/CDHDEFAULT/Ready"
cudb_pm_path = "/fs/var/log/esa/pm3gppXml"
sgsn_ebs_dir = '/fs/tmp/OMS_LOGS/ebs/ready/'
sgsn_uetrace_dir = '/fs/tmp/OMS_LOGS/ue_trace/ready/'
sgsn_ctum_dir = '/fs/tmp/OMS_LOGS/ctum/ready/'
NON_EVENT_FIVEG_NODES = [ "VPP", "VRC", "RNNODE", "5GRADIONODE", "VRM" ]
STATS_ONLY_NE_TYPES = [ "CSCF", "EPG-SSR", "EPG-EVR", "M-MGW", "MTAS", "SBG", "TCU03", "TCU04", "MRSV", "HSS-FE", "IPWORKS", "MRFV", "UPG", "WCG", "DSC", "VPP", "VRC", "RNNODE", "WMG", "RBS", "STN", "EME", "VTFRADIONODE", "5GRADIONODE", "VRM" ]
STATS_ONLY_NE_TYPES_LOCAL = [ "SPITFIRE", "R6274", "R6672", "R6673", "R6675", "R6371", "R6471-1", "R6471-2" ]
PLAYBACK_ONLY_NE_TYPES = ["FrontHaul"]
TSP_ONLY_NE_TYPES = [ "SAPC-TSP", "MTAS-TSP", "HSS-FE-TSP", "CSCF-TSP" ]
hostname=''
sim_list = []
mme_list = []
playback_list = []
sim_nodes_dict = dict()


def get_sim_data():
    """ retrieves simulation data from /netsim/genstats/tmp/sim_data.txt file

        Returns:
           list: sim data
    """
    try:
       sim_data_file = open(SIM_DATA_FILE, "r")
    except:
       logging.error("cannot find " + SIM_DATA_FILE)
       exit(1)
    sim_data_list = sim_data_file.readlines()
    return sim_data_list

def lastQuarterUTCRegex():
    """ Calculate the regex for last 15 mins alinged to ROP generation time(00,15,30,45 mins) in UTC timezone

        Returns:
           list: one min and 15 min ROP UTC regex
    """
    global lastQuarterStartTime, lastQuarterEndTime
    oneMinuteRegex = []
    presentTime = datetime.datetime.utcnow()
    diffFromLastQuarter = presentTime.minute % 15
    lastQuarterEndTime = presentTime - datetime.timedelta(minutes=diffFromLastQuarter)
    lastQuarterStartTime = lastQuarterEndTime - datetime.timedelta(minutes=15)

    '''A20180322.1345*1400*'''
    fifteenMinRegex = lastQuarterStartTime.strftime("[A-Z]%Y%m%d.%H%M*") + lastQuarterEndTime.strftime("%H%M*")
    for mins in range(0,15):
        ropStartTime = lastQuarterStartTime + datetime.timedelta(minutes=mins)
        ropEndTime = lastQuarterStartTime + datetime.timedelta(minutes=mins+1)
        ropRegex = ropStartTime.strftime("[A-Z]%Y%m%d.%H%M*") + ropEndTime.strftime("%H%M*")
        oneMinuteRegex.append(ropRegex)

    oneMinuteRegex.append(fifteenMinRegex)
    return oneMinuteRegex

def lastQuarterLocalRegex():
    """ Calculate the regex for last 15 mins alinged to ROP generation time(00,15,30,45 mins) in Local timezone

        Returns:
           list: one min and 15 min ROP Local regex
    """
    oneMinuteRegex = []
    presentTime = datetime.datetime.now()
    diffFromLastQuarter = presentTime.minute % 15
    lastQuarterEndTime = presentTime - datetime.timedelta(minutes=diffFromLastQuarter)
    lastQuarterStartTime = lastQuarterEndTime - datetime.timedelta(minutes=15)

    '''A20180322.1345*1400*'''
    fifteenMinRegex = lastQuarterStartTime.strftime("[A-Z]%Y%m%d.%H%M*") + lastQuarterEndTime.strftime("%H%M*")
    for mins in range(0,15):
        ropStartTime = lastQuarterStartTime + datetime.timedelta(minutes=mins)
        ropEndTime = lastQuarterStartTime + datetime.timedelta(minutes=mins+1)
        ropRegex = ropStartTime.strftime("[A-Z]%Y%m%d.%H%M*") + ropEndTime.strftime("%H%M*")
        oneMinuteRegex.append(ropRegex)

    oneMinuteRegex.append(fifteenMinRegex)
    return oneMinuteRegex


def scanDir(sim, dir, child_dir, fileTypeRegex, timeRegex, startedNodesList):
    """ Calculate the number of files present in pm path as per file and rop regex.
        This func also checks for the availability of all the pm paths

        Returns:
           string: number of files in dir : all pm dir present or not
    """

    pmDirPresent = False
    numOfFiles = 0
    numOfPmDir = 0

    allPmDirs = glob.glob(dir + "/*/" + child_dir)
    pmPresentNodes = [pmDir.split(dir)[1].split(child_dir)[0].strip("/") for pmDir in allPmDirs]


    if set(startedNodesList).issubset(set(pmPresentNodes)) and len(pmPresentNodes) is not 0 and len(startedNodesList) is not 0 :
        pmDirPresent = True

    if fileTypeRegex is 'RNC_CTR':

        for ropRegex in timeRegex:
           fileLookup = glob.glob(dir + "/*/" + child_dir + "/" + ropRegex + "*_CellTrace_*") + glob.glob(dir + "/*/" + child_dir + "/" + ropRegex + "*Lrat*") + glob.glob(dir + "/*/" + child_dir + "/" + ropRegex + "*_CTR_*")
           numOfFiles += len(fileLookup)

    else:
        for ropRegex in timeRegex:
           fileLookup = glob.glob(dir + "/*/" + child_dir + "/" + ropRegex + fileTypeRegex)
           numOfFiles += len(fileLookup)

    return str(numOfFiles) + ":" + str(pmDirPresent)


def fetchPmDir(sim, simFullName, sim_data, timeRegexLocal, timeRegexUTC, playbacksim, startedNodesCount):
    """ This functions calls for scanDir function and pass various regex based on types of node

        Returns:
           dictionary: availability of pm path and different number of pm files as applicable
    """

    allPMDirPresent = "NO"
    pm_data = "/c/pm_data/"
    pm_path = ''
    node_type = ''

    scannedStatsResult = []
    scannedCellTraceResult = []
    scannedUeTraceResult = []
    scannedGPEHResult = []
    scannedEbsResult = []



    startedNodesList = getSimNodeDict(simFullName)

    for sim_info in sim_data:
        if simFullName in sim_info:
            sim_info = sim_info.split()
            node_type = sim_info[5]
            stats_dir = sim_info[9]
            trace_dir = sim_info[11]

    if 'lte' in simFullName.lower() and node_type.upper() not in NON_EVENT_FIVEG_NODES:
        parent_dir = TMPFS_DIR + sim

        scannedStatsResult = scanDir(simFullName, parent_dir, stats_dir, '*xml*', timeRegexUTC, startedNodesList).split(":")
        if 'MSRBS-V1' in node_type or 'PRBS' in node_type:
            cell_trace_pattern = '*.Lrat_*'
        else:
            cell_trace_pattern = '*CellTrace_*'
        scannedCellTraceResult = scanDir(simFullName, parent_dir, trace_dir, cell_trace_pattern, timeRegexUTC, startedNodesList).split(":")
        scannedUeTraceResult = scanDir(simFullName, parent_dir, trace_dir, '*_uetrace_*', timeRegexUTC, startedNodesList).split(":")

        if startedNodesCount is not '0' and scannedStatsResult[1] and scannedCellTraceResult[1] and  scannedUeTraceResult[1] :
            allPMDirPresent = "YES"

        return({'allPMDirPresent':allPMDirPresent, 'statsCount':scannedStatsResult[0], 'cellTraceCount':scannedCellTraceResult[0], 'ueTraceCount':scannedUeTraceResult[0]})


    elif 'sgsn' in simFullName.lower():
        parent_dir = NETSIM_DBDIR + simFullName

        scannedStatsResult = scanDir(simFullName, parent_dir, "/fs" + stats_dir, '*xml*', timeRegexLocal, startedNodesList).split(":")
        scannedEbsResult = scanDir(simFullName, parent_dir, sgsn_ebs_dir, '*', timeRegexLocal, startedNodesList).split(":")
        scannedUeTraceResult = scanDir(simFullName, parent_dir, sgsn_uetrace_dir, '*', timeRegexLocal, startedNodesList).split(":")
        scannedCtumResult = scanDir(simFullName, parent_dir, sgsn_ctum_dir, '*', timeRegexLocal, startedNodesList).split(":")

        if startedNodesCount is not '0' and scannedCtumResult[1] and scannedStatsResult[1] and scannedEbsResult[1] and  scannedUeTraceResult[1] :
            allPMDirPresent = "YES"
        return({'allPMDirPresent':allPMDirPresent, 'statsCount':scannedStatsResult[0], 'EBSCount':scannedEbsResult[0], 'ueTraceCount':scannedUeTraceResult[0], 'ctumCount':scannedCtumResult[0]})

    elif 'rnc' in simFullName.lower():
        parent_dir = TMPFS_DIR + sim

        scannedStatsResult = scanDir(simFullName, parent_dir, stats_dir, '*xml*', timeRegexUTC, startedNodesList).split(":")
        scannedCellTraceResult = scanDir(simFullName, parent_dir, trace_dir, "RNC_CTR", timeRegexUTC, startedNodesList).split(":")
        scannedUeTraceResult = scanDir(simFullName, parent_dir, trace_dir, '*_UETR_*', timeRegexUTC, startedNodesList).split(":")
        scannedGPEHResult = scanDir(simFullName, parent_dir, trace_dir + "/p*", '*_GPEH*', timeRegexUTC, startedNodesList).split(":")

        if startedNodesCount is not '0' and scannedStatsResult[1] and scannedCellTraceResult[1] and  scannedUeTraceResult[1] and scannedGPEHResult[1] :
            allPMDirPresent = "YES"
        return({'allPMDirPresent':allPMDirPresent, 'statsCount':scannedStatsResult[0], 'cellTraceCount':scannedCellTraceResult[0], 'ueTraceCount':scannedUeTraceResult[0], 'GPEHCount':scannedGPEHResult[0]})

    elif playbacksim:
        parent_dir = NETSIM_DBDIR + simFullName
        if 'hlr' in simFullName.lower():
            scannedStatsResult = scanDir(simFullName, parent_dir, "/apfs" + hlr_ready_path, '*xml*', timeRegexUTC, startedNodesList).split(":")
        elif 'cudb' in simFullName.lower():
            scannedStatsResult = scanDir(simFullName, parent_dir, cudb_pm_path, '*xml*', timeRegexUTC, startedNodesList).split(":")
        else:
            for ne_type in PLAYBACK_ONLY_NE_TYPES:
                if ne_type.upper() in simFullName.upper():
                   pm_path = fetchNetsimCfgParam(ne_type + "_PM_FileLocation")
            if pm_path:
                pm_data = pm_path.strip("\"")
            if any(NE in simFullName.upper() for NE in TSP_ONLY_NE_TYPES):
                scannedStatsResult = scanDir(simFullName, parent_dir, "/fs" + tsp_opt_path, '*xml*', timeRegexUTC, startedNodesList).split(":")
            elif 'fs/' in pm_data:
                scannedStatsResult = scanDir(simFullName, parent_dir, "/" + pm_data, '*xml*', timeRegexUTC, startedNodesList).split(":")
            else:
                scannedStatsResult = scanDir(simFullName, parent_dir, "/fs" + pm_data, '*xml*', timeRegexUTC, startedNodesList).split(":")

    elif 'bsc' in simFullName.lower():
        parent_dir = NETSIM_DBDIR + simFullName
        scannedStatsResult = scanDir(simFullName, parent_dir, bsc_ready_path, '*xml*', timeRegexUTC, startedNodesList).split(":")

    elif 'msc' in simFullName.lower():
        parent_dir = NETSIM_DBDIR + simFullName
        scannedStatsResult = scanDir(simFullName, parent_dir, msc_ready_path, '*xml*', timeRegexUTC, startedNodesList).split(":")

    elif node_type.upper() in STATS_ONLY_NE_TYPES:
        parent_dir = TMPFS_DIR + simFullName

        scannedStatsResult = scanDir(simFullName, parent_dir, stats_dir, '*xml*', timeRegexUTC, startedNodesList).split(":")
        '''5g node uetrace'''

    elif node_type.upper() in STATS_ONLY_NE_TYPES_LOCAL:
        parent_dir = TMPFS_DIR + simFullName

        scannedStatsResult = scanDir(simFullName, parent_dir, stats_dir, '*xml*', timeRegexLocal, startedNodesList).split(":")

    if len(scannedStatsResult) > 0 and scannedStatsResult[1] :
        allPMDirPresent = "YES"
        return({'allPMDirPresent':allPMDirPresent, 'statsCount':scannedStatsResult[0]})


def getNetsimCfgValues():
    """ This functions fetches required values from netsim_cfg file

        Returns:
           NA
    """
    global hostname,sim_list,mme_list,playback_list
    hostname = fetchNetsimCfgParam("SERVERS").strip("\"").replace("-","_")
    sim_list = fetchNetsimCfgParam("LIST").strip("\"").split()
    mme_list = fetchNetsimCfgParam("MME_SIM_LIST").strip("\"").split()
    playback_list = fetchNetsimCfgParam("PLAYBACK_SIM_LIST").strip("\"").split()

def getTotalNodes(sim):
    """ Calculates total number of nodes present for a given simulation

        Returns:
           integer:total number of nodes
    """

    simdir = NETSIM_DBDIR+sim

    if os.path.isdir(NETSIM_DBDIR+sim):
        return len(os.walk(NETSIM_DBDIR+sim).next()[1])
    else:
        return 0

def getStartedNodes(sim):
    """ Calculates total number of started nodes for a given simulation from /tmp/showstartednodes.txt

        Returns:
           integer:total number of started nodes
    """

    command = "grep " + sim + " " + SHOW_STARTED_NODES + " | wc -l"
    return Popen(command, stdout= PIPE, shell=True).communicate()[0].strip("\n")

def getSimNodeDict(sim):
    """ Gives the names of started node for a given simulation

        Returns:
           List:names of started node
    """
    nodeList = []

    command = "grep " + sim + " " + SHOW_STARTED_NODES
    one_sim_info_list = Popen(command, stdout= PIPE, shell=True).communicate()[0].split("\n")

    for oneNodeInfo in one_sim_info_list:
        one_node_info_list = oneNodeInfo.strip().split()


        if len(one_node_info_list) > 0:
            nodeName = one_node_info_list[0].strip()
            nodeList.append(nodeName)

    return nodeList

def main(argv):
    output_details = {}
    totalNodes = 0
    getNetsimCfgValues()
    simListDbDir = os.listdir(NETSIM_DBDIR)

    sim_data_list  = get_sim_data()

    timeRegexUTC = lastQuarterUTCRegex()
    timeRegexLocal = lastQuarterLocalRegex()

    all_sims = sim_list + mme_list + playback_list

    rop = lastQuarterStartTime.strftime("%Y%m%d.%H%M") + "-" +  lastQuarterEndTime.strftime("%H%M")
    for sim in all_sims:


        simFullName = sim
        if not "-" in sim:
            simFullName = ' '.join(s for s in simListDbDir if sim in s)
            simContainingList = simFullName.split()
            if len(simContainingList) > 1:
                for simulation in simContainingList:
                    simNameElementsList = simulation.split('-')
                    if sim in simNameElementsList:
                       simFullName = simulation
            else:
                simFullName = simFullName
        totalNodes = getTotalNodes(simFullName)
        startedNodesCount = getStartedNodes(simFullName)
        if simFullName not in playback_list:
            pmDirData = fetchPmDir(sim, simFullName, sim_data_list, timeRegexLocal, timeRegexUTC, False, startedNodesCount)
        else:
            pmDirData = fetchPmDir(sim, simFullName, sim_data_list, timeRegexLocal, timeRegexUTC, True, startedNodesCount)
        if pmDirData is not None:
            if output_details:
                simDetails = dict(chain({'simName' : simFullName, 'totalNodes' : totalNodes, 'startedNodes' : startedNodesCount}.items(),pmDirData.items()))
                output_details['Server']['simulations'].append(simDetails)

            else:
                output_details = {'ROPvalue' : rop,'Server':{'serverName' : hostname, 'simulations' : [dict(chain({'simName' : simFullName, 'totalNodes' : totalNodes, 'startedNodes' : startedNodesCount}.items(), pmDirData.items()))]}}
    
    INSTRUMENTATION_LOG = INSTRUMENTATION_DIR + "genstatsInstrumentation_" + str(lastQuarterStartTime.strftime("%Y%m%d")) + ".json"
    with open(INSTRUMENTATION_LOG, 'a+') as outfile:
        outfile.seek(0,2)
        if outfile.tell() == 0 :
            json.dump([output_details], outfile, indent=4)
        else :
            outfile.seek(-1,2)
            outfile.truncate()
            outfile.write(' , ')
            json.dump(output_details,outfile, indent=4)
            outfile.write(']')

if __name__ == "__main__":
    main(sys.argv[1:])
