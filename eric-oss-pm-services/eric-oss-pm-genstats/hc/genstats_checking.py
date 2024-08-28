#!/usr/local/bin/python2.7
# encoding: utf-8

################################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 23.10
# Purpose       :  Script verifies if Genstats is configured correctly as per the netsim_cfg. Also, checks if there are no ACTIVE Scanners present on Netsim end for any node.
# Jira No       :  NSS-43371
# Gerrit Link   :  https://gerrit.ericsson.se/14895481
# Description   :  Adding support for 15 min default and 5 mins flex PCC/PCG 2h cyclical file replay
# Date          :  29/03/2023
# Last Modified :  vadim.malakhovski.ext@ericsson.com
####################################################

'''
genstats_checking -- shortdesc

genstats_checking is a description

It defines classes_and_methods

@author:     eaefhiq

@copyright:  2018 ericsson. All rights reserved.

@license:    ericsson

@contact:    liang.e.zhang@ericsson.com
@deffield    updated: Updated
'''

import sys
import os
from multiprocessing import Pool
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging, subprocess
from GenstatsLteSimPmVerifier import GenstatsLteSimPmVerifier
from GenstatsSgsnSimPmVerifier import GenstatsSgsnSimPmVerifier
from GenstatsWranSimPmVerifier import GenstatsWranSimPmVerifier
from GenstatsSimPmStatsVerifier import GenstatsSimPmStatsVerifier
from GenstatsGsmSimPmVerifier import GenstatsGsmSimPmVerifier
import subprocess
from subprocess import PIPE, Popen
from GenstatsConfigurablePmVerifier import GenstatsConfigurablePmVerifier

__all__ = []
__version__ = 0.1
__date__ = '2016-04-12'
__updated__ = '2016-04-12'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

LOG_FILE = '/netsim/genstats/logs/genstatsQA.log'
NETSIM_DBDIR = '/netsim/netsim_dbdir/simdir/netsim/netsimdir/'
TMPFS = '/pms_tmpfs/'
GENSTATS_LOG_DIR = '/netsim_users/pms/logs/'
GENSTATS_CONSOLELOGS_DIR='/netsim/genstats/logs/rollout_console/'
GENSTATS_CONSOLELOGS_FABTASK='/tmp/genstats.log'
NETSIM_CFG = '/netsim/netsim_cfg'
SIM_DATA_FILE = '/netsim/genstats/tmp/sim_data.txt'
SIM_INFO_FILE = '/netsim/genstats/tmp/sim_info.txt'
STATS_ONLY_NE_TYPES = [ "CSCF", "EPG-SSR", "EPG-EVR", "M-MGW", "MTAS", "SBG", "VSBG", "SPITFIRE", "TCU03", "TCU04", "MRSV", "MRS", "HSS-FE", "IPWORKS", "MRFV", "UPG", "WCG", "DSC", "VPP", "VRC", "RNNODE", "WMG", "RBS", "STN", "EME", "VTFRADIONODE", "R6274", "R6672", "R6673", "R6675", "R6371", "R6471-1", "R6471-2","R6273", "VRM", "VRSM", "VSAPC", "VTIF", "PCC", "PCG", "SHARED-CNF", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "SMSF", "VNSDS", "CONTROLLER6610", "CIMS" ]
startedNodesFile = "/tmp/showstartednodes.txt"
PLAYBACK_ONLY_NE_TYPES = ["FrontHaul_6020","FrontHaul_6080", "BSP", "vDU", "RDM" ]
NON_EVENT_FIVEG_NODES = [ "VPP", "VRC", "RNNODE", "5GRADIONODE", "VRM", "VRSM", "VSAPC", "VTIF", "PCC", "PCG", "SHARED-CNF", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "SMSF", "vDU", "cIMS" ]
CONF_EVENTS_NE = ['5GRADIONODE', 'GNODEBRADIO']
TSP_ONLY_NE_TYPES = [ "SAPC-TSP", "MTAS-TSP", "HSS-FE-TSP", "CSCF-TSP" ]
CMCC_ONLY_NE_TYPES = [ "UDM", "UDR", "NRF", "NSSF" ]
EDE_STATS_SIM = ["LTE", "RNC"]
IMS_NODE_TYPES = [ "CSCF", "SBG", "MTAS", "VBGF", "MRF", "WCG", "DSC" ]
ROUTER_NODE_TYPES = ["R6274", "R6672", "R6673", "R6675", "R6371", "R6471-1", "R6471-2", "R6273"]
PLAYBACK_FLEX_NODE_TYPES = [ "EPG-OI", "vEPG-OI","FrontHaul-6000" ]
COMMON_FLEX_SIM_LIST = ["VSAPC", "SGSN" ]
#Node types with default 24 hours ROPs in MT
FLEX_NODE_TYPES = IMS_NODE_TYPES + ROUTER_NODE_TYPES + COMMON_FLEX_SIM_LIST
#Nodes types having optional 24 hours ROPs in MT
OPTIONAL_FLEX_NODE_TYPES = ["BSC", "vMSC-HC", "vMSC", "MSC-BSC-BSP", "MSC-BC-IS", "HLR-FE-IS", "HLR-FE-BSP", "IPWORKS", "HSS-FE", "UPG", "PCC", "PCG", "MRS"]
IMS_NODE_TYPES_NRM = [ "MTAS", "DSC" ]
FLEX_ROUTER_NODE_TYPES_NRM = [ "R6672", "R6675", "SPITFIRE" ]
EDE_STATS_RADIO = [ "VPP", "VRC", "RNNODE", "5GRADIONODE", "VTFRADIONODE", "VRM", "VRSM", "VSAPC", "VTIF", "PCC", "PCG", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "SMSF", "vDU" ]
IGNORED_FLEX_ROP_STRINGS = ['5', '30', '60', '120', '720']
IGNORED_FLEX_ROP_STRINGS_PLAYBACK = ['5', '30', '60', '120', '720']
NSS_ONLY_NE_TYPES = ['CCES', 'SMSF', 'VNSDS', 'R6273', 'R6673', 'CONTROLLER6610', "SHARED-CNF", "CIMS"]
WMG_OI_NE_TYPE=['WMG-OI', 'VWMG-OI']
DO_SUPPORTED_NODE_TYPES=["SGSN", "VSAPC", "DSC", "GNODEBRADIO", "UPG", "CSCF", "CCRC", "CCES", "CCSM", "SC", "HSS-FE", "CCDM", "CCPC", "vWMG-OI", "vEPG-OI", "vAFG", "VCUDB", "PCC", "PCG"]
### ADD OTHER DELIVERED SUPPORTED NE TYPES IN MD_1 + MAY NOT NEED THIS LIST AT ALL
NSS_AND_MD_1_SUPPORTED_NODE_TYPES=["SCEF", "VCU-UP", "VCU-CP"]

epoch_start_time = None
current_epoch_time = None 
simlist = None

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def run_shell_command(command):
    command_output = Popen(command, stdout=PIPE, shell=True).communicate()[0]
    return command_output

def check_stats_files(sims, nr_list, lte_uetrace='', playbacksimlist='', edeStatsCheck=False , dpltype="NSS"):
    if os.path.isfile(startedNodesFile):
        pool = Pool(2)
        for sim in sims:
            if '-' not in sim or '_' not in sim:
                if sim.replace('.','').isdigit():
                    logging.error("Simulation " + sim + " has been installed with VERSION ID. Why to worry, Please contact SIMNET team.")
                    continue
            if sim in open(startedNodesFile).read():
                ''''check nodes in the simulation'''
                pool.apply_async(check_stats_each_node, (sim, nr_list, lte_uetrace, playbacksimlist,edeStatsCheck,dpltype,))
        pool.close()
        pool.join()

def check_bandwith_limiting(set_bandwith_limiting="OFF"):
    p = subprocess.Popen(["sudo", "-S", "/netsim_users/pms/bin/limitbw",
                          "-n", "-s"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    result = len(p.communicate("shroot\n")[0].strip().split("\n"))
    if set_bandwith_limiting == 'OFF':
        logging.info("BANDWIDTH LIMITING is OFF")
    else:
        logging.info("BANDWIDTH LIMITING is ON. Bandwidth will be set as per the values mentioned in netsim_cfg")


def check_logfile(logfile):
    with open(logfile) as txtfile:
        for line in reversed(txtfile.readlines()):
            if 'failed' in line.lower() and 'file exists' not in line.lower() and 'failed to create symbolic link' in line.lower() or 'error' in line.lower():
                return False
    return True


def verify_logfile(isVapp=False):
    result = []
    logfiles = os.listdir(GENSTATS_LOG_DIR)
    logfiles = filter(None,logfiles)
    consolelogfiles = os.listdir(GENSTATS_CONSOLELOGS_DIR)
    consolelogfiles = filter(None,consolelogfiles)
    check_contains_list = [ 'genstats', 'lte_rec', 'gengpeh', 'genrbsgpeh', 'playbacker', 'limitbw', 'scanners', 'gsm_rec', 'sim_pm_path' ]
    for logfile in logfiles:
        if any( x in logfile.lower() for x in check_contains_list ):
            if not check_logfile(GENSTATS_LOG_DIR + logfile):
                result.append(GENSTATS_LOG_DIR + logfile)
    for logfile in consolelogfiles:
        if 'genstats' in logfile.lower():
            if not check_logfile(GENSTATS_CONSOLELOGS_DIR + logfile):
                result.append(GENSTATS_CONSOLELOGS_DIR + logfile)
    if os.path.isfile(GENSTATS_CONSOLELOGS_FABTASK):
        if not check_logfile(GENSTATS_CONSOLELOGS_FABTASK):
            result.append(GENSTATS_CONSOLELOGS_FABTASK)
    return result

def getSimType(sim):
    sim_type = None
    if os.path.isfile(SIM_INFO_FILE):
        with open(SIM_INFO_FILE, 'r') as sim_info:
            for line in sim_info:
                line = line.replace('\n', '').strip().split(':')
                if line[0] == sim:
                    sim_type = line[1].strip()
                    return sim_type
    return sim_type

def check_flex_nodes(FLEX_LIST, isPlayback):
    flex_sims = []
    for sim in simlist:
        if isPlayback:
            if any(ne.upper() in sim.upper() for ne in PLAYBACK_FLEX_NODE_TYPES) and "TSP" not in sim.upper() and "SBG-IS" not in sim.upper():
                flex_sims.append(sim)
        else:
            ne = getSimType(sim)
            if ne:
                if ne in FLEX_LIST:
                    flex_sims.append(sim)
    return flex_sims


def check_stats_each_node(simname, nr_list, lte_uetrace='', playbacksimlist='', edeStatsCheck=False, dpltype='NSS'):
    pm_data = "/c/pm_data/"
    bsc_ready_path = "/data_transfer/destinations/CDHDEFAULT/Ready/"
    msc_ready_path = "/apfs/data_transfer/destinations/CDHDEFAULT/Ready/"
    tsp_opt_path = "/opt/telorb/axe/tsp/NM/PMF/reporterLogs"
    hlr_ready_path = "/data_transfer/destinations/CDHDEFAULT/Ready"
    vcudb_pm_path = "/fs/home/cudb/oam/performanceMgmt/output"
    if dpltype.startswith("NRM"):
        cudb_pm_path = vcudb_pm_path
    else:
        cudb_pm_path = "/fs/var/log/esa/pm3gppXml"
    cmcc_pm_path = "/fs/PerformanceManagementReportFiles"
    wmg_oi_pm_path = "/fs/var/performance/"
    epg_pm_path = "/fs/var/performance"
    eir_fe_pm_path = "/fs/home/eir/oam/performanceMgmt/output/"
    esc_node_strings = ['ERSN', 'ERS_SN_SCU', 'ERS_SN_ESC', 'SCU_']
    scef_pm_path_string = "A:/fs/cluster/pm3gppxml/:zip|B:/fs/cluster/PMAgent/aggregated/:xml"
    vcuup_pm_path = "/fs/PerformanceManagementReportFiles"
    vcucp_pm_path = "/fs/PerformanceManagementReportFiles"
    vdu_pm_path = "/fs/PerformanceManagementReportFiles"
    rdm_pm_path = "/fs/PerformanceManagementReportFiles"
    adp_pm_path = "/fs/PerformanceManagementReportFiles"
    ecee_pm_path = "/fs/var/cache/pmreports"
    fronthaul_6000_pm_path = "/fs/mnt/sd/ecim/enm_performance"
    node_type = ""

    for sim_info in open(SIM_DATA_FILE):
        sim_info = sim_info.split()
        if sim_info[1].strip().endswith(simname):
            if "RNC" in sim_info[1].upper() and sim_info[1].strip().endswith(sim_info[3].strip()):
                rnc_stats_dir = sim_info[9]
            else:
                node_type = sim_info[5]
                stats_dir = sim_info[9]
                trace_dir = sim_info[11]
                break
    if edeStatsCheck:
        for ede_sim in EDE_STATS_SIM:
            if ede_sim in simname.upper() and node_type.upper() not in EDE_STATS_RADIO:
                return
            elif "rbs" in simname.lower() and node_type.lower() == "rbs":
                return
    """ x object for stats, y for evenst for five g sims """
    x = GenstatsSimPmVerifier(TMPFS, simname, pm_data)
    y = GenstatsSimPmVerifier(TMPFS, simname, pm_data)
    x.set_epoch_time(epoch_start_time)
    y.set_epoch_time(epoch_start_time)
    x.set_current_epoch_time(current_epoch_time)
    y.set_current_epoch_time(current_epoch_time)

    if 'sgsn' in simname.lower():
        x = GenstatsSgsnSimPmVerifier(NETSIM_DBDIR, simname, "/fs" + pm_data)
    elif node_type is not "" and 'lte' in simname.lower() and node_type.upper() not in NON_EVENT_FIVEG_NODES:
        x = GenstatsLteSimPmVerifier(TMPFS, simname, stats_dir, trace_dir, lte_uetrace, node_type)
    elif node_type in CONF_EVENTS_NE:
        x = GenstatsSimPmStatsVerifier(TMPFS, simname, stats_dir)
        x.verify()
        if deploymenttype != 'DO':
            y = GenstatsConfigurablePmVerifier(simname, node_type, nr_list, dpltype)
            y.verify()
        return
    elif 'rnc' in simname.lower():
        x = GenstatsWranSimPmVerifier(TMPFS, simname, stats_dir, rnc_stats_dir)
    elif playbacksimlist is not None and simname in playbacksimlist:
        #Order of vcudb and cudb must remain as below (vcudb first, cudb after)
        if 'eir-fe' in simname.lower():
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, eir_fe_pm_path)
        elif 'vcudb' in simname.lower():
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, vcudb_pm_path)
        elif 'cudb' in simname.lower():
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, cudb_pm_path)
        elif 'epg-oi' in simname.lower():
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, epg_pm_path)
        ### sims supported by NSS and MD_1 but not by NRM
        elif any(substring in simname.upper() for substring in NSS_AND_MD_1_SUPPORTED_NODE_TYPES):
            if deploymenttype in ['NSS', 'MD_1']:
                if 'scef' in simname.lower():
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, scef_pm_path_string)
                elif 'vcu-up' in simname.lower():
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, vcuup_pm_path)
                elif 'vcu-cp' in simname.lower():
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, vcucp_pm_path)
            else:
                logging.warn("%s  simulation is not supported in NRM and DO deployments", simname)
        elif 'vdu' in simname.lower():
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, vdu_pm_path)
        elif 'rdm' in simname.lower() and deploymenttype == 'NSS':
            x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, rdm_pm_path)
        elif 'ecee' in simname.lower():
            if deploymenttype == 'NSS':
               x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, ecee_pm_path)
            else:
               logging.info("%s  simulation is not supported in NRM deployment", simname)
        elif 'adp' in simname.lower():
            if deploymenttype == 'NSS':
                x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, adp_pm_path)
            else:
                return
        elif 'fronthaul-6000' in simname.lower():
            if deploymenttype == 'NSS':
                x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, fronthaul_6000_pm_path)
            else:
                logging.warn("%s  simulation is not supported in NRM deployment", simname)
        else:
            for ne_type in PLAYBACK_ONLY_NE_TYPES:
                if edeStatsCheck == True and  "FRONTHAUL" in ne_type.upper() :
                    return
                if ne_type.upper().replace("_","-") in simname.upper():
                    pm_path = run_shell_command("grep  "+ ne_type + "_PM_FileLocation " + NETSIM_CFG).strip()
                    if pm_path:
                         pm_data = pm_path.split("=")[-1].replace("\"", "")
            if any(NE in simname.upper() for NE in TSP_ONLY_NE_TYPES):
                x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname,"/fs" + tsp_opt_path)
            elif any(NE in simname.upper() for NE in CMCC_ONLY_NE_TYPES):
                x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname,cmcc_pm_path)
            elif any(NE in simname.upper() for NE in WMG_OI_NE_TYPE):
                if deploymenttype in ['NSS','DO']:
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, wmg_oi_pm_path)
                else:
                    logging.info("%s  simulation is not supported in NRM deployment", simname)
            elif 'fs/' in pm_data:
                x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname,"/" + pm_data)
            else:
                if 'vafg' in simname.lower() and deploymenttype not in ['NSS','DO']:
                    logging.info("%s  simulation is not supported in " + deploymenttype + " deployment ", simname)
                elif deploymenttype == 'DO' and node_type.upper() not in DO_SUPPORTED_NODE_TYPES:
                    logging.info("%s  simulation is not supported in " + deploymenttype + " deployment ", simname)
                elif deploymenttype in ['NSS','DO']:
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, "/fs" + pm_data)
                elif 'SBG-IS' not in simname.upper() and 'FRONTHAUL' not in simname.upper():
                    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, "/fs" + pm_data)
    #The below method is for handling GSM sims which contains MSC, BSC nodes or MSC, vBSC nodes
    elif 'msc' in simname.lower():
        if 'vbsc' in simname.lower():
           if deploymenttype == "NSS":
              x = GenstatsGsmSimPmVerifier(NETSIM_DBDIR, simname, msc_ready_path)
           else:
              logging.info("%s  simulation is not supported in NRM deployment", simname)
        else:
            x = GenstatsGsmSimPmVerifier(NETSIM_DBDIR, simname, msc_ready_path)
    #The below method is for handling standalone BSC sims i.e., a sim which contains only BSC nodes
    elif 'bsc' in simname.lower():
        x = GenstatsGsmSimPmVerifier(NETSIM_DBDIR, simname, "/apfs" + bsc_ready_path)
    elif 'hlr' in simname.lower():
        x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, "/apfs" + hlr_ready_path)
    #Suppressing Genstats HC for ESC node types as False error get popped up if files pushes to ENM during HC run
    #elif any(name in simname.upper().replace('-','_') for name in esc_node_strings):
    #    x = GenstatsSimPmStatsVerifier(NETSIM_DBDIR, simname, "/fs" + pm_data)
    elif deploymenttype == 'DO' and node_type.upper() not in DO_SUPPORTED_NODE_TYPES:
        logging.info("%s  simulation is not supported in " + deploymenttype + " deployment ", simname)
    elif node_type.upper() in STATS_ONLY_NE_TYPES:

        if node_type.upper() in NSS_ONLY_NE_TYPES and deploymenttype != 'NSS':
            if node_type.upper()== "CCES" and deploymenttype == "DO" :
                x = GenstatsSimPmStatsVerifier(TMPFS, simname, stats_dir)
            else:
                logging.info("%s node type is not supported in NRM deployment", node_type.upper())
        else:
            x = GenstatsSimPmStatsVerifier(TMPFS, simname, stats_dir)


    x.verify()


def check_crontab(expected_stats_work_load_list, expected_rec_work_load_list,expected_playback_work_load_list, expected_gpeh_work_load_list=[], expected_rbs_gpeh_work_load_list=[], wran=False, gpeh=False, rbs_gpeh=False, dpltype="NSS"):
    p = subprocess.Popen(["crontab", "-l"], stdout=subprocess.PIPE)
    (output, error) = p.communicate()
    p.stdout.close()

    global IGNORED_FLEX_ROP_STRINGS, IGNORED_FLEX_ROP_STRINGS_PLAYBACK
    if dpltype != "NSS":
        if dpltype == "MD_1":
            IGNORED_FLEX_ROP_STRINGS.remove('5')
        else:
            # IGNORE flex 1 min ROP for ROUTER nodes in RV
            if check_flex_nodes(FLEX_ROUTER_NODE_TYPES_NRM, False):
                if not check_flex_nodes(IMS_NODE_TYPES_NRM, False):
                    IGNORED_FLEX_ROP_STRINGS += ['1']
    else:
        # IGNORE flex 24 hours ROPS in MT for Optional Flex nodes nodes
        if check_flex_nodes(OPTIONAL_FLEX_NODE_TYPES, False):
            if not check_flex_nodes(FLEX_NODE_TYPES, False):
                IGNORED_FLEX_ROP_STRINGS += ['1440']
        if check_flex_nodes(OPTIONAL_FLEX_NODE_TYPES, True):
            if not check_flex_nodes(PLAYBACK_FLEX_NODE_TYPES, True):
                IGNORED_FLEX_ROP_STRINGS_PLAYBACK += ['1440']

    stats_work_load_list = [line.split()[7] for line in output.splitlines(
    ) if "/netsim_users/pms/bin/genStats" in line and not line.startswith("#") and line.split()[7] not in IGNORED_FLEX_ROP_STRINGS ]
    rec_work_load_list = [line.split()[7] for line in output.splitlines(
    ) if "/netsim_users/pms/bin/lte_rec.sh" in line and not line.startswith("#")]
    playback_work_load_list = [line.split()[7] for line in output.splitlines(
    ) if "/netsim_users/pms/bin/startPlaybacker.sh" in line and not line.startswith("#") and line.split()[7] not in IGNORED_FLEX_ROP_STRINGS_PLAYBACK ]
    if not any("/netsim_users/pms/bin/flexrop.sh" in line for line in output.splitlines()):
       logging.error("The Flexible rop script is not enabled.")

    if os.path.isfile('/netsim_users/pms/etc/flex_rop_cfg'):
       with open('/netsim_users/pms/etc/flex_rop_cfg', 'r') as fin:
           for line in fin:
               line = line.rstrip()
               if '#!/bin/bash' not in line:
                   script = line.split('_')[2]
                   rop = line.split('_')[1]
                   if rop == '1440' and script == 'GENSTATS':
                      stats_work_load_list += ['1440']
                   elif rop == '1440' and script == 'PLAYBACK':
                        playback_work_load_list += ['1440']

    if dpltype == "NSS":
        if not (set(expected_stats_work_load_list) == set(stats_work_load_list) and set(rec_work_load_list) == set(expected_rec_work_load_list) and set(expected_playback_work_load_list) == set(playback_work_load_list)):
            logging.error(
                "The ROP setup is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)
    elif dpltype == "MD_1":
        if not (set(expected_stats_work_load_list) == set(stats_work_load_list)):
            logging.error(
                "The ROP setup is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)
    else:
        if not (set(expected_stats_work_load_list) == set(stats_work_load_list) and set(expected_playback_work_load_list) == set(playback_work_load_list)):
            logging.error(
                "The ROP setup is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)
    if wran:
        wran_rec_work_load_list = [line.split()[9] for line in output.splitlines(
        ) if "/netsim_users/pms/bin/wran_rec.sh" in line and not line.startswith("#")]
        if not (set(wran_rec_work_load_list) == set(expected_rec_work_load_list)):
            logging.error(
                "The ROP setup for wran is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)
    if gpeh:
        gpeh_work_load_list = [line.split()[9] for line in output.splitlines(
        ) if "/netsim_users/pms/bin/genGPEH" in line and not line.startswith("#")]
        if not (set(gpeh_work_load_list) == set(expected_gpeh_work_load_list)):
            logging.error(
                "The ROP setup for gpeh is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)
    if rbs_gpeh:
        rbs_gpeh_work_load_list = [line.split()[7] for line in output.splitlines(
        ) if "/netsim_users/pms/bin/genRbsGpeh" in line and not line.startswith("#")]
        if not (set(rbs_gpeh_work_load_list) == set(expected_rbs_gpeh_work_load_list)):
            logging.error(
                "The ROP setup for rbs gpeh is different between Crontab and /netsim/netsim_cfg.")
            os.system('echo  "ERROR crontab entry misconfiguration " >> ' + LOG_FILE)

def is_nodetype_in_simlist(nodeType, simlist):
    if os.path.isfile(startedNodesFile):
        for sim in simlist:
            if sim in open(startedNodesFile).read():
                if nodeType in sim.lower():
                    if not check_for_wcdma_pico_node(sim):
                        if int(sim.replace('RNC','')) < 21:
                            return True
    return False


def check_for_wcdma_pico_node(sim):
    sim_name = ''
    node_type = ''
    for sim_info in open(SIM_DATA_FILE):
        sim_name = sim_info.split()[1]
        if 'RNC' in sim_name:
           sim_name = sim_name.split('-')[-1]
           node_type = sim_info.split()[5]
           if sim == sim_name:
               if node_type == 'PRBS':
                   return True
               elif node_type == 'RNC':
                   continue
               else:
                   return False
    return False


def is_gpeh_in_rnc(gpehmpcells, simlist):
    if gpehmpcells is not None:
        gpehmaxcell = [x.split(":")[1] for x in gpehmpcells]
        for sim in simlist:
            if 'rnc' in sim.lower():
                rnc_num = sim.lower().split('rnc')[1]
                if 'rnc' in sim.lower() and int(max(gpehmaxcell)) >= int(rnc_num):
                    return True
    return False


def get_nrat_sim_list():
    with open(NETSIM_CFG, 'r') as f:
        for line in f:
            if line.startswith('NRAT_LTE_UETRACE_LIST'):
                return [ data.split(':')[1] for data in line.split('"')[1].split() ]
    return None

def check_daily_rop_playback_sim():
    with open(NETSIM_CFG, 'r') as f:
        for line in f:
            if line.startswith('PLAYBACK_SIM_LIST'):
                if "FrontHaul" in line:
                    return True

def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  COPYRIGHT Ericsson 2016

  The copyright to the computer program(s) herein is the property of
  Ericsson Inc. The programs may be used and/or copied only with written
  permission from Ericsson Inc. or in accordance with the terms and
  conditions stipulated in the agreement/contract under which the
  program(s) have been supplied.

USAGE
''' % (program_shortdesc)

    # try:
    # Setup argument parser
    parser = ArgumentParser(
        description=program_license, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        '-l', '--simlist', dest='simlist', help='simulation list', nargs='+', type=str)
    parser.add_argument('-ul', '--uetracelist', dest='uetracelist',
                        help='uetracelist list', nargs='+', type=str)
    parser.add_argument(
        '-b', '--bandwithlim', dest='bandwithlim', help='bandwith limiting', type=str)
    parser.add_argument('-recwl', '--recworkload', dest='recwl',
                        help='recording work load list', nargs='+', type=str)
    parser.add_argument('-statswl', '--statsworkload', dest='statswl',
                        help='stats work load list', nargs='+', type=str)
    parser.add_argument('-gpehwl', '--gpehworkload', dest='gpehwl',
                        help='gpeh work load list', nargs='+', type=str)
    parser.add_argument('-rbsgpehwl', '--rbsgpehworkload', dest='rbsgpehwl',
                        help='rbs gpeh work load list', nargs='+', type=str)
    parser.add_argument('-gpehmpcells', '--gpehmpcellslist', dest='gpehmpcells',
                        help='gpeh mp cells list', nargs='+', type=str)
    parser.add_argument('-playbacksimlist', '--playbacksimlist', dest='playbacksimlist',
                        help='playback sim list', nargs='+', type=str)
    parser.add_argument('-deployment', '--deployment', dest='deployment',
                        help='deployment type', nargs='+', type=str)
    parser.add_argument('-edeStatsCheck', '--edeStatsCheck', dest='edeStatsCheck',
                        help='edeStatsCheck type', nargs='+', type=str)
    parser.add_argument('-periodicHC', '--periodicHC', dest='periodicHC', help='periodic Health check condition', nargs='+', type=str)
    parser.add_argument('-epoch_time', '--epoch_time', dest='epoch_time', help='contain script initialization epoch time', nargs='+', type=str)
    parser.add_argument('-current_time', '--current_time', dest='current_time', help='gives current script runtime, for checking future files exist', nargs='+', type=str)

    # Process arguments
    args = parser.parse_args()
    global simlist
    simlist = args.simlist
    uetracelist = args.uetracelist
    bandwithlim = args.bandwithlim
    statsworkload = args.statswl
    recworkload = args.recwl
    gpehworkload = args.gpehwl
    rbsgpehworkload = args.rbsgpehwl
    gpehmpcellslist = args.gpehmpcells
    playbacksimlist = args.playbacksimlist
    global deploymenttype
    deploymenttype = args.deployment[0]
    periodicHC = args.periodicHC[0]

    global epoch_start_time
    epoch_start_time = args.epoch_time[0]
    global current_epoch_time
    current_epoch_time = args.current_time[0]

    if "False" in str(args.edeStatsCheck):
        edeStatsCheck = False
    else:
        edeStatsCheck = True

    nrat_ue_sim_list = None
    if deploymenttype == 'NSS':
        nrat_ue_sim_list = get_nrat_sim_list()

    # logging.info("Following nodes are not started: %s",str(GenstatsSimPmVerifier.get_all_not_started_nes()))
    check_stats_files(simlist, nrat_ue_sim_list, uetracelist, playbacksimlist, edeStatsCheck, dpltype=deploymenttype)
    check_bandwith_limiting(bandwithlim)

    isgpehEnabled = False
    isrbsgpehEnabled = False

    playback_work_load = []
    playback_work_load += statsworkload

    if "NSS" in deploymenttype:
        if check_flex_nodes(FLEX_NODE_TYPES, False):
            statsworkload += ['1440:ALL']
        if check_flex_nodes(PLAYBACK_FLEX_NODE_TYPES, True):
            playback_work_load += ['1440:ALL']
    elif "NRM" in deploymenttype:
        if check_flex_nodes(IMS_NODE_TYPES_NRM, False):
            statsworkload += ['1440:ALL', "1:ALL"]
        if check_daily_rop_playback_sim():
            playback_work_load += ['1440:ALL']

    if is_nodetype_in_simlist("rnc", simlist):
        if is_gpeh_in_rnc(gpehmpcellslist, simlist):
            if not (gpehworkload is None):
                isgpehEnabled = True
            if not (rbsgpehworkload is None):
                isrbsgpehEnabled = True

        check_crontab([x.split(":")[0] for x in statsworkload],
                      [x.split(":")[0] for x in recworkload], [x.split(":")[0] for x in playback_work_load], [x.split(":")[0] for x in gpehworkload], [x.strip() for x in rbsgpehworkload], True, isgpehEnabled, isrbsgpehEnabled, dpltype=deploymenttype)
    
    if (statsworkload is not None and recworkload is not None):
        if deploymenttype == "MD_1":
            check_crontab([x.split(":")[0] for x in statsworkload],dpltype=deploymenttype)
        else:
            check_crontab([x.split(":")[0] for x in statsworkload], [
                      x.split(":")[0] for x in recworkload], [x.split(":")[0] for x in playback_work_load], dpltype=deploymenttype)

    import platform
    if str(periodicHC).upper() == 'FALSE':
        try:
            result = verify_logfile(platform.node() == 'netsim')
            if result:
                error_message = str(result)
                logging.error('Log files have error: %s', error_message)
                os.system('echo  "ERROR ' + error_message + '" >> ' + LOG_FILE)
        except:
            logging.error(' Genstats log files are missing!')

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:

        sys.exit(0)
    sys.exit(main())


