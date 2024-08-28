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
# Version no    :  NSS 18.16
# Purpose       :  Purpose of this script is to find the configuration for cell trace file generation.
# Jira No       :  NSS-20364
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4222660/
# Description   :  To find configuration for 5GRADIONODE
# Date          :  8/10/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

from _collections import defaultdict
from multiprocessing import Pool
import traceback

from dumpMoTreeCommands import DumpMoTreeCommand
from utilityFunctions import Utility


# Defining class objects
utilObj = Utility()
dumpMoObj = DumpMoTreeCommand()

tmp_netsim_cfg = '/tmp/' + utilObj.getHostName()

""" celltrace_node_param_map (dict) = { "node_type" : [list of paramters ... ]} """
celltrace_node_param_map = {'FIVEGRADIONODE' : ['EventProducer'], 'GNODEBRADIO' : ['EventProducer']}

""" celltrace_sim_node_map (dict) = { "sim_name|node_type" : [list of node directories with full path ]} """
celltrace_sim_node_map = defaultdict(list)

""" celltrace_fetched_config_map (dict) = { "node_type" : [list of param with associated value ... i.e param|value]} """
celltrace_fetched_config_map = defaultdict(list)

"""  final resultant map , celltrace_final_config_map (dict) = { "sim_name|node_type" : [list of directory path(s)] } """
celltrace_final_config_map = {}

def getIgnoredValues(ne, inList):
    """ Returns filtered list
    """
    try:
        if ne == 'FIVEGRADIONODE':
            ignoredList = ['1', 'RC']
            return [ val.strip() for val in inList if val.strip() not in ignoredList]
        elif ne == 'GNODEBRADIO':
            networkFnList = ['CUCP', 'CUUP', 'DU']
            return [val.strip() for val in inList if val.strip() in networkFnList ]
        else:
            return inList
    except:
        traceback.print_exc()


def executeDumpMoCommand(sim, ne_type, node, def_path, defStr):
    """ This method will execute command on netsim_shell to get the EventProducer values and based on those values it will
        execute the command on netsim shell for events pm path associated to the events producer.
    """
    try:
        pathList, file_pull_id = [], '1'
        fetchEventProducerCommand = "printf '.open " + sim + "\n.select " + node + "\n" + dumpMoObj.getEventProducer.replace('REPLACE_NODE_NAME', node) + "' | " + utilObj.netsim_script + " | grep EventProducer | awk -F'=' '{print $2}'"
        totalProducerValues = filter(None, utilObj.run_shell_command(fetchEventProducerCommand).split())
        finalProducerList = getIgnoredValues(ne_type, totalProducerValues)
        if len(finalProducerList) > 0:
            if ne_type == 'GNODEBRADIO':
                file_pull_id = '2'
            fetchOutputPathCommand = "printf '.open " + sim + "\n.select " + node + "\n" + dumpMoObj.getCelltraceOutputDir.replace('REPLACE_NODE_NAME', node).replace('REPLACE_PM_FILE_PULL_CAP_ID', file_pull_id) + "' | " + utilObj.netsim_script + " | grep 'outputDirectory=' | awk -F'=' '{print $2}'"
            for producer in finalProducerList:
                path = utilObj.run_shell_command(fetchOutputPathCommand.replace('EVENT_PRODUCER_ID', producer)).strip()
                if path:
                    path = utilObj.reCorrectPmPath(path)
                    if not path.endswith('/'):
                        pathList.append(path + '/')
                    else:
                        pathList.append(path)
                else:
                    if ne_type == 'GNODEBRADIO':
                        pathList.append(def_path + producer + '/')
                    else:
                        pathList.append(def_path + '/' + producer + '/')
        else:
            return createAndSendDefaultPath(ne_type, def_path, defStr)
        return pathList
    except:
        traceback.print_exc()


def createAndSendDefaultPath(ne, def_path, vals):
    if ne == 'FIVEGRADIONODE':
        return [ def_path + '/' + path + '/' for path in vals.split()]
    elif ne == 'GNODEBRADIO':
        return [ def_path + path + '/' for path in vals.split()]


def validateNratSimulation(sim, node):
    command = ''
    for name, value in dumpMoObj.gNodeBRadioNode_nrat_set_command_map.items():
        command = "printf '.open " + sim + "\n.select " + node + "\n" + value[0].replace('REPLACE_NODE_NAME', node) + "' | " + utilObj.netsim_script + " | grep -i -w '" + value[1] + "'"
        if utilObj.run_shell_command(command).strip():
            return True
    return False
    

def findConfigurationFromNetsimShell(sim_info):
    """ This method will find the events_pm_path from getting EventProducer names from Netsim shell """
    try:
        node_list = celltrace_sim_node_map[sim_info]
        sim_info_elements = sim_info.split('|')
        sim_name, node_type = sim_info_elements[0], sim_info_elements[1]
        default_path = utilObj.default_event_pm_path[node_type]
        serachStr = celltrace_node_param_map[node_type][0]
        for element in celltrace_fetched_config_map[node_type]:
            if element.startswith(serachStr):
                serachStr = element.split('|')[1]
                break
        if not node_list:
            return sim_info, createAndSendDefaultPath(node_type, default_path, serachStr)
        else:
            for node_path in node_list:
                node_name = utilObj.getBasename(node_path)
                if utilObj.checkForNodeStatus(node_name, utilObj.startedNodeInfoFile):
                    return sim_info, executeDumpMoCommand(sim_name, node_type, node_name, default_path, serachStr)
                    """
                    if node_type == 'GNODEBRADIO':
                        if validateNratSimulation(sim_name, node_name):
                            return sim_info, executeDumpMoCommand(sim_name, node_type, node_name, default_path, serachStr)
                        else:
                            return sim_info, []
                    else:
                        return sim_info, executeDumpMoCommand(sim_name, node_type, node_name, default_path, serachStr)
                    """
            if node_type == 'GNODEBRADIO':
                return sim_info, []
            else:
                return sim_info, createAndSendDefaultPath(node_type, default_path, serachStr)
    except:
        traceback.print_exc()


def createJsonFile(inMap):
    """ This method will create a JSON file, which will contains all the configuration.
    """
    json_file = utilObj.celltrace_json
    utilObj.removeFilesIfExists(json_file)
    utilObj.writeJsonFileFromInputMap(inMap, json_file)


def collect_result(result):
    """ This method will collect the result of invoked multi processed instance. """
    global celltrace_final_config_map
    if result[1]:
        celltrace_final_config_map[result[0]] = result[1]


def findCelltraceConfguration():
    """ This method invoke the other method in multi process way to fetch data from dumpMo command and will create the map
        celltrace_final_config_map (dict) = { "sim_name|node_type" : [list of directory path(s)] }
    """
    if celltrace_sim_node_map:
        pool_size = Pool(utilObj.getActualMpInstance())
        for sim_info in celltrace_sim_node_map.keys():
            pool_size.apply_async(findConfigurationFromNetsimShell, args=(sim_info,), callback=collect_result)
        pool_size.close()
        pool_size.join()
        createJsonFile(celltrace_final_config_map)
    else:
        utilObj.printStatements('No simulation found with configurable celltrace generation.', 'WARNING', True)


def findPmsNodeDirectories(sim_name, node_type):
    """ This method will find pms path and will return node list with full path
    """
    pms_path = utilObj.getPmsPathForSim(sim_name, node_type)
    return utilObj.getherNodeList(pms_path, sim_name)


def readNetsimCfgForConfiguration():
    """ This method will read the /tmp/netsim_cfg to find required parameter and will create the map
        celltrace_fetched_config_map (dict) = { "node_type" : [list of param with associated value ... i.e param|value]}
    """
    if utilObj.checkFileExistance(tmp_netsim_cfg):
        global celltrace_fetched_config_map
        with open(tmp_netsim_cfg, 'r') as cfg_file:
            for line in cfg_file:
                for node_type, params in celltrace_node_param_map.items():
                    for param in params:
                        if line.startswith(node_type.replace('-','_') + '_' + param):
                            celltrace_fetched_config_map[node_type].append(param + '|' + line.split('"')[1].strip())
    else:
        utilObj.printStatements(tmp_netsim_cfg + ' not found.', 'ERROR', True)


def readSimDataFileAndFindRequiredInfo():
    """ This method find the required simulation for which celltrace needs to configured from sim_data file and will
        create the map celltrace_sim_node_map (dict) = { "sim_name|node_type" : [lis of node directories with full path ]}
    """
    if utilObj.checkFileExistance(utilObj.startedNodeInfoFile):
        if utilObj.checkFileExistance(utilObj.sim_data_file):
            global celltrace_sim_node_map
            with open(utilObj.sim_data_file, 'r') as sim_data:
                for line in sim_data:
                    line = line.split()
                    if line[5] == '5GRADIONODE':
                        line[5] = 'FIVEGRADIONODE'
                    if line[5] in celltrace_node_param_map:
                        node_dir_list = findPmsNodeDirectories(line[1], line[5])
                        if not node_dir_list:
                            utilObj.printStatements('Node directories not found for ' + line[1] + '. Will set default celltrace configuration.', 'WARNING')
                        celltrace_sim_node_map[line[1] + '|' + line[5]] = node_dir_list
        else:
            utilObj.printStatements(utilObj.sim_data_file + ' not found.', 'WARNING', True)
    else:
        utilObj.printStatements(utilObj.startedNodeInfoFile + ' file not found. Skipping process of finding configurable celltrace parameters.', 'WARNING', True)


utilObj.printStatements('Started execution to find data for configurable cell trace generation.', 'INFO')

readSimDataFileAndFindRequiredInfo()
readNetsimCfgForConfiguration()
findCelltraceConfguration()

utilObj.printStatements('Finished execution to find data for configurable cell trace generation.', 'INFO')
