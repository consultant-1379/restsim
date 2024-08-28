#!/usr/bin/python

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
# Version no    :  NSS 23.01
# Purpose       :  Script verify for the configuarble event file generation
# Jira No       :  NSS-41094 
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/13746073/
# Description   :  Adding support to check RNC parent and child nodes through respective PM dir
# Date          :  03/11/2022
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################

'''
Created on 13 Apr 2016

@author: eaefhiq
'''
import os, sys, datetime, glob, abc, logging, subprocess, time
from collections import defaultdict

# Adding utility script path in system path
sys.path.insert(0, '/netsim_users/auto_deploy/bin/')

from utilityFunctions import Utility

logging.basicConfig(format='%(levelname)-8s %(message)s', level=logging.INFO)
LOG_FILE = '/netsim/genstats/logs/genstatsQA.log'

initial_epoch_time = datetime.datetime.utcfromtimestamp(0)
local_epoch = datetime.datetime.fromtimestamp(0)
start_epoch_time = 0
current_epoch_time = 0 

class GenstatsSimPmVerifier(object):
    '''
    classdocs
    '''
    NETSIM_DBDIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
    SIM_INFO_FILE = '/netsim/genstats/tmp/sim_info.txt'
    
    util = Utility()

    linked_node_types_NRM = ["EPG-SSR", "EPG-EVR"]
    linked_node_types = ["SGSN"]
    if "NSS" not in util.getDeploymentType():
        linked_node_types += linked_node_types_NRM

    def __init__(self, tmpfs_dir, simname, pm_data_dir):
        '''
        Constructor
        '''
        self.tmpfs_dir = tmpfs_dir
        self.simname = simname
        self.pm_data_dir = pm_data_dir

    def set_epoch_time(self, start_epoch):
        global start_epoch_time
        start_epoch_time = int(start_epoch) - 1

    def set_current_epoch_time(self, current_epoch):
        global current_epoch_time
        current_epoch_time = int(current_epoch)

    @abc.abstractmethod
    def verify(self):
        return

    def get_nodes_file_not_generated(self, nodename_list=[], data_dir='', reg='*', rnc_parent_dir=''):
        result = []
        for nodename in nodename_list:
            if 'RNC' in self.simname.upper() and self.simname.strip().endswith(nodename.strip()):
                pm_data_path = self.tmpfs_dir + \
                    self.simname + '/' + nodename + rnc_parent_dir
            elif 'BSC' in self.simname.upper() and 'MSRBS' in nodename:
                pm_data_path = self.tmpfs_dir + \
                    self.simname + '/' + nodename + '/fs/c/pm_data'
            else:
                pm_data_path = self.tmpfs_dir + \
                    self.simname + '/' + nodename + data_dir
           
            timestamp_of_the_latest_file = self.get_the_latest_file_timestamp_by_regx(
                pm_data_path, reg)
            self.mountingPointVerifier(self.simname, nodename, data_dir)
            # print nodename, pm_data_path, timestamp_of_the_latest_file
            if not self.verify_file_timestamp(timestamp_of_the_latest_file):
                result.append(nodename)
        return result
    def mountingPointVerifier(self, sim_name, node_name, data_dir):
        for sim in os.listdir(self.NETSIM_DBDIR):
            if sim.endswith(sim_name):
                sim_name = sim
                break
        data_dir = data_dir if data_dir.startswith("/fs") else "/fs/"+data_dir
        file_path = self.NETSIM_DBDIR + sim_name + "/"+ node_name + data_dir
        file_path = file_path.replace("//","/")
        if os.path.ismount(file_path):
            message = "Warning : path not mounted properly "+file_path
            os.system('echo \"' + message + '\" >> ' + LOG_FILE)
    def getStartedNodeListForSim(self, sim_name, pms_path, inputNodeList):
        if not inputNodeList:
            logging.warning('No node directory found for sim : ' + sim_name + ' in pms path : ' + pms_path)
        else:
            startedNodes = []
            for nodeDir in inputNodeList:
                node_name = os.path.basename(nodeDir)
                if self.util.checkForNodeStatus(node_name, self.util.startedNodeInfoFile):
                    startedNodes.append(nodeDir)
            if not startedNodes:
                logging.warning('No started node found for sim : ' + sim_name)
                return []
            else:
                return startedNodes
    
    def checkFilesNotGeneratedForNodes(self, nodeDataPathList, pm_path, reg='*'):
        result = []
        for nodePath in nodeDataPathList:
            timestamp_of_the_latest_file = self.get_the_latest_file_timestamp_by_regx(
                nodePath, reg)
            # print nodename, pm_data_path, timestamp_of_the_latest_file
            pm_path = nodePath.split("/")[1:]
            sim_name, node_name, pm_path = pm_path[1], pm_path[2], "/".join(pm_path[3:])
            self.mountingPointVerifier(sim_name, node_name, pm_path)
            if not self.verify_file_timestamp(timestamp_of_the_latest_file):
                nodePath = nodePath.replace(pm_path, '').split('/')[1]
                result.append(nodePath)
        result = list(set(result))
        return result
    
            
    def getConfiguredPath(self, sim_name, node_type, startedneList):
        if not startedneList:
            logging.warning('No nodes started for sim : ' + sim_name)
            return []
        if not os.path.isfile(self.util.celltrace_json):
            logging.error(self.util.celltrace_json + ' file not present for sim : ' + sim_name)
            return []
        jsonMapObject = self.util.getJsonMapObjectFromFile(self.util.celltrace_json)
        if not jsonMapObject:
            logging.error('No JSON object found for sim : ' + sim_name)
            return []
        pm_path_list = self.util.getEnrichedJsonDataFromKey(jsonMapObject, sim_name + '|' + node_type)[1]
        if not pm_path_list:
            logging.error('No directory List found for configurable events path for sim : ' + sim_name)
            return []
        return [ node_path + str(pm_path) for node_path in startedneList for pm_path in pm_path_list]


    def check_tmpfs_setup(self, simulation):
        result = self.__get_tmpfs_setup_result(simulation)
        return self.__get_fs_off_nodes(result)

    '''get trace file range  e.g. 154kb_ue_trace.gz:LTE01:1:4:1:64   the range is between 1 and  4'''

    def get_trace_file_range(self, trace_list):
        result = {}
        for x in trace_list:
            nodename = x.split(':')[1]
            result[nodename] = xrange(
                int(x.split(':')[2]), (int(x.split(':')[3]) + 1))
        return result

    def check_node_in_range(self, nodename, index_range):
        node_index = int(nodename[-5:])
        return node_index in index_range

    '''from the files that their names match the given regular expression in the directory to get the latest created file & get the file timestamp'''

    def get_the_latest_file_timestamp_by_regx(self, directory, reg):
        try:
            if not os.listdir(directory):
                return datetime.datetime.utcnow() - datetime.timedelta(weeks=54)
            '''get the latest created file path'''
            'For hardlink paths need to get epoch time from file timestamp'
            if any(x in directory for x in self.linked_node_types): 
                filename_to_epoch_map = defaultdict(str)
                for filepath in glob.iglob(directory + "/" + reg):
                    latestfile = os.path.basename(filepath)
                    startDate = latestfile.split(".")[0][1:]
                    startTime = latestfile.split(".")[1].split("+")[0]
                    start_date_format = datetime.datetime(int(startDate[:4]), int(startDate[4:6]), int(startDate[6:8]), int(startTime[:2]), int(startTime[2:]))
                    start_epoch=start_date_format.strftime('%s')
                    'Ignore future files'
                    if int(start_epoch) <= int(current_epoch_time):
                        filename_to_epoch_map[start_epoch] = filepath
                latestfile_path = filename_to_epoch_map[max(filename_to_epoch_map, key=filename_to_epoch_map.get)]
            elif 'semaphore' == reg:
                latestfile_path = max(
                    [filename for filename in glob.iglob(directory+"/"+"*") if "xml" not in filename and int(os.lstat(filename).st_ctime) <= current_epoch_time], key=lambda x: os.lstat(x).st_ctime)
            else:
                latestfile_path = max([filepath for filepath in glob.iglob(directory+"/"+reg) if int(os.lstat(filepath).st_ctime) <= current_epoch_time], key=lambda x: os.lstat(x).st_ctime)
            return datetime.datetime.utcfromtimestamp(os.lstat(latestfile_path).st_ctime)
        except (ValueError):
            'if there is no file generated in the directory, then this exception is thrown. It returns a time stamp one year ago'
            return datetime.datetime.utcnow() - datetime.timedelta(weeks=54)

    '''to verify if the file is created in last 1 minute.'''

    def verify_file_timestamp(self, latest_file_datetime):
        deltaOfFileCreationToInitialEpochInDateTime = latest_file_datetime - initial_epoch_time
        deltaInSeconds = int(deltaOfFileCreationToInitialEpochInDateTime.seconds + (deltaOfFileCreationToInitialEpochInDateTime.days * 24 * 3600))
        return (deltaInSeconds >= start_epoch_time)

    def find_started_nodes(self, reg="([0-9]{1,3}[\.]){3}[0-9]{1,3}"):
        started_nodes_proc = self.pipe_to_netsim(
            self.netsim_showstarted(), True)
        started_nodes_proc = subprocess.Popen(
            ["grep", "-E", reg], stdin=started_nodes_proc.stdout, stdout=subprocess.PIPE)
        # started_nodes_proc.stdout.close()
        started_node_txt = started_nodes_proc.communicate()[0]
        result = {}
        for line in started_node_txt.splitlines():
            sim_name = line.split()[-1].split("/")[-1]
            node_name = line.split()[0]
            result.setdefault(sim_name, []).append(node_name)
        # logging.debug(str(result))
        return result

    def report_error(self, error_msg, check_fun, *args):
        try:
            result = check_fun(*args)
            if result:
                logging.error(error_msg + " %s", str(result))
                nodes_with_error = str(result)
                message = "ERROR " + error_msg + nodes_with_error
                os.system('echo \"' + message + '\" >> ' + LOG_FILE)
        except:
            logging.error(error_msg)

    def __get_tmpfs_setup_result(self, simulation):
        # logging.debug("tmpfs checking start at %s",simulation)
        return self.pipe_to_netsim(self.netsim_show_fs(simulation))[0]

    def __get_fs_off_nodes(self, tmpfs_setup_result):
        result = []
        tmp = ''
        flag = False

        for line in tmpfs_setup_result.splitlines():
            if line.startswith('LTE'):
                flag = True
                tmp = line.split()[0].strip()[:-1]
            elif line.strip() == '':
                flag = False
            elif flag:
                if 'tmpfs' in line and 'off' in line:
                    result.append(tmp)
        return result

    @staticmethod
    def findKey(key, keys):
        for temp in keys:
            if key == temp.split('-')[-1]:
                return temp

    @staticmethod
    def pipe_to_netsim(netsim_cmd, pipe_flag=False):
        p = subprocess.Popen(
            ["echo", "-n", netsim_cmd], stdout=subprocess.PIPE)
        netsim_pipe_p = subprocess.Popen(
            ["/netsim/inst/netsim_pipe"], stdin=p.stdout, stdout=subprocess.PIPE)
        p.stdout.close()
        if pipe_flag:
            return netsim_pipe_p
        else:
            return netsim_pipe_p.communicate()

    @staticmethod
    def get_all_not_started_nes():
        result = []
        output = GenstatsSimPmVerifier.pipe_to_netsim(
            GenstatsSimPmVerifier.netsim_show_allsimnes())[0]
        for line in output.splitlines():
            if 'not started' in line:
                result.append(line.split()[0])
        return result

    @staticmethod
    def netsim_showstarted():
        return '''.show started\n'''

    @staticmethod
    def netsim_show_fs(simulation):
        return '''.open %s\n.select network \n.show fs\n''' % (simulation)

    @staticmethod
    def nesim_show_numstartednes_per_simulation():
        return '''.show numstartednes -per-simulation\n'''

    @staticmethod
    def nesim_show_numstartednes():
        return '''.show numstartednes\n'''

    @staticmethod
    def netsim_show_allsimnes():
        return '''.show allsimnes\n'''

    @staticmethod
    def get_all_started_nes_by_type(node_type):
        p_started_nodes = subprocess.Popen(['perl', '-ne', 'if(/(\S+)(\s+)\d{3}.*$/i){print "$1\n";}'], stdin=GenstatsSimPmVerifier.pipe_to_netsim(
            GenstatsSimPmVerifier.netsim_showstarted(), True).stdout, stdout=subprocess.PIPE)
        output = subprocess.Popen(
            ['grep', '-i', node_type], stdin=p_started_nodes.stdout, stdout=subprocess.PIPE).communicate()[0]
        p_started_nodes.stdout.close()
        return output.splitlines()


