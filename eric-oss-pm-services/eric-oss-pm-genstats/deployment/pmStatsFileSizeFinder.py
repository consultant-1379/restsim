#!/usr/bin/python
################################################################################
# COPYRIGHT Ericsson 2021
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 23.07
# Purpose       :  Script compares stats file sizes generated on the server with expected ones stored in cfg file
# Jira No       :  NSS-43554
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/14770733/
# Description   :  Added one condition to differentiate the CUDB pm paths in MT and RV
# Date          :  16/03/2023
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################


"""
Generates  a file .... containing the following data below on each simulation

HOST_NAME: <HOST_NAME> SIM_NAME: <SIM_NAME>  NE_TYPE: <NE_TYPE>  FILE_EXTN: <FILE_EXTN> FILES/ROP: <FILES/ROP> EXP. AVG SIZE/ROP: <EXP. AVG SIZE/ROP> ACT. AVG SIZE/ROP: <ACT. AVG SIZE/ROP> RESULT: <RESULT>

"""

from _collections import defaultdict
import os, sys, getopt, socket
from subprocess import Popen, PIPE
from multiprocessing import Pool
from shutil import rmtree
from getopt import getopt, GetoptError
from glob import glob
from time import sleep, time
from utilityFunctions import Utility

util = Utility()

HOSTNAME = socket.gethostname()
IP_ADDRESS = None

resultant_map = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : defaultdict(list))))
SIM_CHAR_MAP = defaultdict(lambda : defaultdict(list))
table_header = ( 'HOST_NAME', 'SIM_NAME', 'NE_TYPE', 'FILE_EXTN', 'FILES/ROP', \
                 'EXP. AVG SIZE/ROP', 'ACT. AVG SIZE/ROP', 'RESULT')
longg = dict(zip((range(len(table_header))),(len(str(x)) for x in table_header)))
table_row_info, sims_not_aligned_list, sims_not_supported_list = [], [], []

ONE_KILO_BYTE, GZ_EXTENSION, COLON_SEP, DECIMAL_PRECISION = 1024.0, '.gz', ':' , '.2f'

checkLatestRopFileSize, entire_status = False, True
master_server, servers = None, None
expected_file_map = {}

db_dir = '/netsim/netsim_dbdir/simdir/netsim/netsimdir/<REPLACE_SIM_NAME>'
SIM_DATA_FILE = '/netsim/genstats/tmp/sim_data.txt'
STARTED_NODE_FILE = '/tmp/showstartednodes.txt'
netsimdir = '/netsim/netsimdir'
result_path = '/tmp/PM_STATS_FILE_SIZE/'
PLAYBACK_CFG = '/netsim_users/pms/bin/playback_cfg'
NETSIM_CFG = '/netsim/netsim_cfg'
SFTP_SCRIPT = '/netsim_users/pms/bin/sftp_framework.sh'
report_csv = result_path + HOSTNAME + '_report.csv'

PM_STATS_FILESIZE_CFG = '/netsim_users/reference_files/ExpectedPMStatsFileSizes/pm_stats_filesize_cfg'
PM_STATS_VERIFICATION_PARAM = 'PM_STATS_VERIFICATION_PARAM'
NE_STATS_MAPPINGS = defaultdict(lambda : defaultdict(list))
DUAL_PM_PATH = ["CUDB"]

def updateFileSizeDict():
    '''
    reads pm file size cfg file and creates a nested dictionary with those values form the file
    NE_STATS_MAPPINGS = { extension : { ne_type : [ min_size, max_size, files_per_rop ] }}
    '''
    
    if not os.path.isfile(PM_STATS_FILESIZE_CFG):
        util.printStatements(PM_STATS_FILESIZE_CFG + ' file not found.', 'ERROR', True)

    with open(PM_STATS_FILESIZE_CFG , 'r') as pm_stats_file:
        for line in pm_stats_file:
            if line.strip() == "" or line.strip().startswith('#'):
                continue
            else:
                elements = line.strip().split(COLON_SEP)
                ne_type, min_size, max_size, files_per_rop, ext = elements[0], elements[1], elements[2], int(elements[3]), elements[4]
                min_size, max_size = (min_size, max_size) if not ne_type == "MTAS" else (min_size.split("_")[0],max_size.split("_")[0]) if int(os.path.getmtime(SIM_DATA_FILE)) in range(int(time())-3600,int(time())) else (min_size.split("_")[1],max_size.split("_")[1]) 
                NE_STATS_MAPPINGS[ext][ne_type] = [float(min_size), float(max_size), files_per_rop]

def reDefineNodeType(inputSim, inputNe):
    '''
    returns edited node type as some node may contain more than 1 node type
    '''
    if inputNe == '5GRADIONODE':
        return 'FIVEGRADIONODE'
    elif inputSim.split('-')[-1].startswith('LTE') and inputNe == 'MSRBS-V2' or inputNe == 'ERBS':
        return 'LTE ' + inputNe
    else:
        return inputNe


def collectSimDataContent():
    '''
    SIM_CHAR_MAP = { sim_name : { ne_type : [ ne_pm_path, file_extension ] }}
    '''
    global sims_not_supported_list
    cellMapDict = defaultdict(lambda : defaultdict(list))
    depl_type = util.getDeploymentVersionInformation()
    if depl_type == 'NRM6.3':
       with open(SIM_DATA_FILE, 'r') as sim_file:
           for line in sim_file:
               line_info = line.split()
               if line_info[5] == 'GNODEBRADIO':
                  cell_count = util.getCellCount(line_info[3])
                  cellMapDict[line_info[1]] = cell_count

    with open(SIM_DATA_FILE, 'r') as sim_file:
        for line in sim_file:
            line_info = line.split()
            line_info[5] = reDefineNodeType(line_info[1], line_info[5].upper())
            for extension, ne_map in NE_STATS_MAPPINGS.iteritems():
                if line_info[5] == 'GNODEBRADIO' and depl_type == 'NRM6.3':
                   line_info[5] = line_info[5] + '_' + str(cellMapDict[line_info[1]])
                if line_info[5] in ne_map:
                    line_info[9] = correct_pm_path(line_info[9])
                    SIM_CHAR_MAP[line_info[1]][line_info[5]] = [line_info[9], extension]
                    if line_info[1] in sims_not_supported_list:
                        sims_not_supported_list = filter(lambda x : x != line_info[1], sims_not_supported_list)
                    break
                else:
                    sims_not_supported_list.append(line_info[1])


def readCFG(param, cfgFile):
    '''
    returns the parameter value from cfg file
    '''
    if os.path.isfile(cfgFile):
        with open(cfgFile, 'r') as cfg:
            for line in cfg:
                if line.startswith(param + '='):
                    return line.strip().split('=')[1].replace('"', '').split('\n')[0]
    return False


def correct_pm_path(inputPath):
    '''
    returns added forward slash at the end of a path for pm paths with one missing
    '''
    if inputPath:
        if not inputPath.endswith('/'):
            return inputPath + '/'
        return inputPath
    else:
        util.printStatements('The PM path is empty.', 'ERROR')


def collectPlaybackSimData():
    '''
    SIM_CHAR_MAP = { sim_name : { ne_type : [ ne_pm_path, file_extension ] }}
    '''
    playback_sim_list = readCFG('PLAYBACK_SIM_LIST', NETSIM_CFG)
    dep_type = readCFG('TYPE', NETSIM_CFG)

    if not playback_sim_list:
        util.printStatements('No Playback Simulation present.', 'INFO')
    for sim_name in playback_sim_list.split():
        for extension, ne_map in NE_STATS_MAPPINGS.iteritems():
            for node_type in ne_map:
                if node_type in sim_name:
                    sim_pm_path = readCFG(node_type.replace('-','_')+'_PM_FileLocation', NETSIM_CFG)
                    if not sim_pm_path:
                        if any(ne_ == node_type for ne_ in DUAL_PM_PATH) and "NRM" in dep_type:
                            sim_pm_path = readCFG(node_type.replace('-','_')+'_STATS_APPEND_PATH_NRM', PLAYBACK_CFG)
                        else:
                            sim_pm_path = readCFG(node_type.replace('-','_')+'_STATS_APPEND_PATH', PLAYBACK_CFG)
                        if not sim_pm_path:
                            util.printStatements('Either file ' + PLAYBACK_CFG + ' not found or parameter ' + node_type.replace('-','_') + '_STATS_APPEND_PATH not found in file.', 'WARNING', True)
                    sim_pm_path = correct_pm_path(sim_pm_path)
                    if node_type in ne_map:
                        SIM_CHAR_MAP[sim_name][node_type] = [sim_pm_path , extension ]
                        break


def gatherStartedNodeData():
    '''
    returns a list of starde nodes
    '''
    started_node_list = []
    with open(STARTED_NODE_FILE, 'r') as started_file:
        for line in started_file:
            line = line.strip()
            if not line.startswith('=') and not line.startswith('#') and netsimdir in line:
                started_node_list.append(line.split()[0])
    return started_node_list

def generateStatisticsForPmStatsFile(inArgs, path, extension):
    '''
    returns gathered and sorted pm files
    inArgs = ( sim_name, ne_type, ne_name )
    collected_data_map : { filename : [ compressed_size, uncompressed_size, uc/c_ratio] }
    '''
    collected_data_map = defaultdict(list)
    if NE_STATS_MAPPINGS['NO_EXT'].get(inArgs[1]):
        # check for multiple PM files in a single dir per ROP
        if 'SBG-IS' in path:
            fileList = glob(path + '*')
        # check for multiple dirs with single PM file per ROP
        elif 'TSP' in path:
            fileList = glob(path + '**/*')
    # check for 1 file per 1 dir per ROP
    else:
        fileList = glob(path + '*' + extension)
        if 'MTAS' in path and int(os.path.getmtime(SIM_DATA_FILE)) in range(int(time())-7200,int(time())):
            fileList = [i for i in fileList if int(os.path.getmtime(i)) in range(int(os.path.getmtime(SIM_DATA_FILE)),int(time()))]
    if checkLatestRopFileSize:
        fileList.sort(key=os.path.getmtime)
        requiredFiles = int(NE_STATS_MAPPINGS[extension][inArgs[1]][2]) * -1
        fileList = fileList[requiredFiles:]
    for fullpath in filter(None, fileList):
        fileName = os.path.basename(fullpath)
        if not os.path.isfile(fullpath):
            continue
        if extension.endswith(GZ_EXTENSION):
            if inArgs[1] in ['EPG-SSR', 'EPG-EVR']:
                file_data = os.path.getsize(fullpath)
                collected_data_map[fileName] = [0, float(format( float(file_data) / ONE_KILO_BYTE, DECIMAL_PRECISION)), 0]
                continue
            file_data = util.run_shell_command('gzip -l ' + fullpath).split('\n')
            file_data = file_data[1].strip().split()
            ''' file data : compressed_size uncompressed_size ratio(uncompressed/compressed) file name'''
            collected_data_map[fileName].append(float(format( float(file_data[0]) / ONE_KILO_BYTE, DECIMAL_PRECISION)))
            collected_data_map[fileName].append(float(format( float(file_data[1]) / ONE_KILO_BYTE, DECIMAL_PRECISION)))
            collected_data_map[fileName].append(float(format( \
                                        collected_data_map[fileName][1]/collected_data_map[fileName][0], DECIMAL_PRECISION)))
        else:
            file_data = os.path.getsize(fullpath)
            collected_data_map[fileName] = [0, float(format( float(file_data) / ONE_KILO_BYTE, DECIMAL_PRECISION)), 0]
    return inArgs, collected_data_map


def collect_result(result):
    '''
    resultant_map = { sim_name : { ne_type : { ne_name : collected_data_map }}}
    collected_data_map = { filename : [ compressed_size, uncompressed_size, uc/c_ratio] }
    '''
    global resultant_map
    resultant_map[result[0][0]][result[0][1]][result[0][2]] = result[1]


def gatherPmStatsData():
    '''
    gathers pm locations of started nodes
    SIM_CHAR_MAP = { sim_name : { ne_type : [ne_pm_path, file_extension ]} }
    '''
    started_node_data = gatherStartedNodeData()
    pool_size = Pool(2)
    for sim_name, ne_values in SIM_CHAR_MAP.iteritems():
        for ne , values in ne_values.iteritems():
            simId, rncFound, rbsFound, erbsFound, msrbsv2Found = '', False, False, False, False
            if ne == 'RNC':
                rncFound, simId = True, sim_name.split('-')[-1]
            elif ne == 'LTE MSRBS-V2':
                msrbsv2Found = True, sim_name.split('-')[-1]
            elif ne == 'LTE ERBS':
                erbsFound = True, sim_name.split('-')[-1]
            elif ne == 'LTE RBS':
                rbsFound = True, sim_name.split('-')[-1]
            sim_path = db_dir.replace('<REPLACE_SIM_NAME>', sim_name)
            for nodeDir in filter(None, os.listdir(sim_path)):
                if rncFound:
                    if nodeDir != simId:
                        continue
                elif msrbsv2Found:
                    if nodeDir == simId:
                        continue
                elif erbsFound:
                    if nodeDir == simId:
                        continue
                elif rbsFound:
                    if nodeDir == simId:
                        continue
                if nodeDir in started_node_data:
                    nodePath = sim_path + '/' + nodeDir + '/fs' + values[0]
                    pool_size.apply_async( \
                        generateStatisticsForPmStatsFile, args=((sim_name, ne, nodeDir), nodePath, values[1]) \
                        , callback=collect_result)
    pool_size.close()
    pool_size.join()


def findNoOfCellsToNode(sim, node):
    '''
    returns count of cells
    '''
    eutranfile = netsimdir + '/' + sim + '/SimNetRevision/EUtranCellData.txt'
    count = 0
    with open(eutranfile, 'r') as e_file:
        for line in e_file:
            line_data = line.strip().split(',')
            if node == line_data[1].split('=')[1]:
                count += 1
    return count


def get_information(f_type, _map):
    return [float(value) for node, child_map in _map.iteritems() \
                                      for type, value in child_map.iteritems() if type == f_type]


def writeDataAsPerStatistics():
    '''
    computes actual  pm file sizes, compares with expected values and outputs the results
    resultant_map = { sim_name : { ne_type : { ne_name : collected_data_map }}}
    collected_data_map = { filename : [ compressed_size, uncompressed_size, uc/c_ratio] }
    '''
    global entire_status
    
    for sim_name , sim_values in resultant_map.iteritems():
        isLte = False
        for node_type, other_values in sim_values.iteritems():
            if node_type in ['LTE MSRBS-V2', 'LTE ERBS']:
                isLte = True
            ext_, divider, avg_values_map = None, 1, defaultdict(lambda : defaultdict())
            for key in NE_STATS_MAPPINGS:
                if node_type in NE_STATS_MAPPINGS[key]:
                    divider = NE_STATS_MAPPINGS[key][node_type][2]
                    ext_ = key
                    break
            detailedStatisticsFile = result_path + sim_name + COLON_SEP + COLON_SEP.join(node_type.split()) + COLON_SEP +'detailedStatistics.csv'
            with open(detailedStatisticsFile, 'w') as f_detail:
                for node_name, value_map in other_values.iteritems():
                    compressed_list, uncompressed_list, ratio_list = [], [], []
                    if isLte:
                        f_detail.write( sim_name + ' | ' + node_type + ' | ' + node_name + ' | ' \
                                        + str(findNoOfCellsToNode(sim_name, node_name)) + '\n')
                    else:
                        f_detail.write( sim_name + ' | ' + node_type + ' | ' + node_name + '\n')
                    f_detail.write( '\n\nFileName | Compressed (KB) | UnCompressed (KB) | Ratio\n' )
                    sortedFileList = sorted(value_map.keys())
                    for filename in sortedFileList:
                        file_props = value_map[filename]
                        compressed_list.append(file_props[0])
                        uncompressed_list.append(file_props[1])
                        ratio_list.append(file_props[2])
                        f_detail.write(filename + ' | ' + str(file_props[0]) + ' | ' + str(file_props[1]) + ' | ' \
                                        + str(file_props[2]) + '\n')
                    try:
                        f_detail.write('\nTotal Files : ' + str(len(value_map)) + '\n')
                        f_detail.write('Minimum Compressed file size : ' + str(min(compressed_list)) + '\n')
                        f_detail.write('Maximum Compressed file size : ' + str(max(compressed_list)) + '\n')
                        f_detail.write('Average Compressed file size : ' + format(sum(compressed_list)/len(value_map), DECIMAL_PRECISION) + '\n')
                        f_detail.write('Average ROP Compressed file size : ' + format(sum(compressed_list)/(len(value_map)/divider), DECIMAL_PRECISION ) + '\n')
                        f_detail.write('Minimum UnCompressed file size : ' + str(min(uncompressed_list)) + '\n')
                        f_detail.write('Maximum UnCompressed file size : ' + str(max(uncompressed_list)) + '\n')
                        f_detail.write('Average UnCompressed file size : ' + format(sum(uncompressed_list)/len(value_map), DECIMAL_PRECISION) + '\n')
                        f_detail.write('Average ROP UnCompressed file size : ' + format(sum(uncompressed_list)/(len(value_map)/divider), DECIMAL_PRECISION) + '\n')
                        f_detail.write('Minimum unComp/Comp ratio : ' + str(min(ratio_list)) + '\n')
                        f_detail.write('Maximum unComp/Comp ratio : ' + str(max(ratio_list)) + '\n')
                        f_detail.write('Average unComp/Comp ratio : ' + format(sum(ratio_list)/len(value_map),DECIMAL_PRECISION) + '\n'*5)
                        avg_values_map[node_name]['COMPRESSED'] = float(format(sum(compressed_list)/len(value_map), DECIMAL_PRECISION))
                        avg_values_map[node_name]['UNCOMPRESSED'] = format(sum(uncompressed_list)/len(value_map), DECIMAL_PRECISION)
                        avg_values_map[node_name]['ROP_COMPRESSED'] = float(format(sum(compressed_list)/(len(value_map)/divider), DECIMAL_PRECISION))
                        avg_values_map[node_name]['ROP_UNCOMPRESSED'] = format(sum(uncompressed_list)/(len(value_map)/divider), DECIMAL_PRECISION)
                        avg_values_map[node_name]['RATIO'] = format(sum(ratio_list)/len(value_map),DECIMAL_PRECISION)
                    except ValueError:
                        util.printStatements('Negative list taken to find the average', 'ERROR')
                        sys.exit()
                temp_comp_list = get_information( 'COMPRESSED' , avg_values_map)
                temp_rop_comp_list = get_information( 'ROP_COMPRESSED' , avg_values_map)
                temp_uncomp_list = get_information( 'UNCOMPRESSED' , avg_values_map)
                temp_rop_uncomp_list = get_information( 'ROP_UNCOMPRESSED' , avg_values_map)
                temp_ratio_list = get_information( 'RATIO' , avg_values_map)

                avg_comp_file_size = round(sum(temp_comp_list)/len(temp_comp_list), 2)
                avg_comp_rop_file_size = round(sum(temp_rop_comp_list)/len(temp_comp_list), 2)
                avg_uncomp_file_size = round(sum(temp_uncomp_list)/len(temp_uncomp_list), 2)
                avg_uncomp_rop_file_size= round(sum(temp_rop_uncomp_list)/len(temp_uncomp_list), 2)

                f_detail.write('Total average Compressed file size : ' \
                                   + str(avg_comp_file_size) + '\n')
                f_detail.write('Total average Compressed ROP file size : ' \
                                   + str(avg_comp_rop_file_size) + '\n')
                f_detail.write('Total average UnCompressed file size : ' \
                                   + str(avg_uncomp_file_size) + '\n')
                f_detail.write('Total average UnCompressed ROP file size : ' \
                                   + str(avg_uncomp_rop_file_size) + '\n')
                f_detail.write('Total average unComp/Comp file size : ' \
                                   + format(sum(temp_ratio_list)/len(temp_ratio_list), DECIMAL_PRECISION) + '\n'*5)

                
                min_size, max_size = round(float(NE_STATS_MAPPINGS[ext_][node_type][0]), 2), round(float(NE_STATS_MAPPINGS[ext_][node_type][1]), 2)
                avg_file_size, file_extension, pm_status = None, ext_, None
                if ext_ == '.xml.gz':
                    if node_type in ['EPG-SSR', 'EPG-EVR']:
                        avg_file_size = avg_uncomp_rop_file_size
                    else:
                        avg_file_size = avg_comp_rop_file_size
                else:
                    avg_file_size = avg_uncomp_rop_file_size
                
                if ext_ == 'NO_EXT':
                    file_extension = 'N/A'
                
                if not (min_size <= avg_file_size <= max_size):
                    pm_status = 'NOT_ALIGNED'
                    entire_status = False
                    sims_not_aligned_list.append(sim_name)
                else:
                    pm_status = 'ALIGNED'
                
                table_row_info.append([HOSTNAME, sim_name, node_type, file_extension, int(divider), \
                                      ' - '.join([ str(x) for x in NE_STATS_MAPPINGS[ext_][node_type][:2]]) + ' KB', \
                                      str(avg_file_size) + ' KB', pm_status])                            


def help_message():
    print '\npython /netsim_users/auto_deploy/bin/pmStatsFileSizeFinder.py -l <YES/NO>\n\nOR\n\npython /netsim_users/auto_deploy/bin/pmStatsFileSizeFinder.py --checkLatestRopFileSize <YES/NO>'
    sys.exit()


def printInformationInTabularFormat():
    for row in table_row_info:
        longg.update(( index, max(longg[index], len(str(element))) ) for index, element in enumerate(row))
    info = ' | '.join('%%-%ss' % longg[i] for i in xrange(0,8))
    print '\n' + '\n'.join((info % table_header,'-|-'.join( longg[i]*'-' for i in xrange(8)), \
                     '\n'.join(info % (a,b,c,d,e,f,g,h) for a,b,c,d,e,f,g,h in table_row_info))) + '\n'
    

def generateCsvReport():
    with open(report_csv, 'w') as r_c:
        r_c.write(','.join(table_header) + '\n')
        for row_data in table_row_info:
            r_c.write(','.join([ str(rd) for rd in row_data]) + '\n')
        r_c.flush()


def doRemoteCopy():
    put_value = '"put ' + report_csv + ' ' + result_path + '"'
    command = SFTP_SCRIPT + ' netsim ' + IP_ADDRESS + ' netsim ' + put_value
    util.run_shell_command(command)


def waitForOtherServersFile():
    global expected_file_map
    all_files_fetched = False
    wait_time = 120
    for server in servers.split('|'):
        expected_file_map[server + '_report.csv'] = False
    wait_time += (( ( len(expected_file_map.keys()) / 25 ) + 1) * 30)
    timeout_time = int(time()) + wait_time
    while int(time()) <= timeout_time:
        fileList = filter(None, os.listdir(result_path))
        for k in expected_file_map:
            if k in fileList:
                expected_file_map[k] = True
        if False not in expected_file_map.values():
            all_files_fetched = True
            util.printStatements('All Remote host files found at ' + result_path, 'INFO')
        sleep(5)
        if all_files_fetched:
            break
    if not all_files_fetched:
        unable_to_fetched_file = []
        for k, v in expected_file_map.iteritems():
            if v == False:
                unable_to_fetched_file.append(k)
        util.printStatements('Timeout happened as not able to fetch files : ' + ', '.join(unable_to_fetched_file) , 'WARNING', True)
    else:
        for k in expected_file_map:
            if k.split('_')[0] != HOSTNAME:
                with open(result_path + k, 'r') as f:
                    next(f)
                    for line in f:
                        table_row_info.append(line.strip().replace('\n', '').split(','))

                            
def main():
    global master_server, servers
    if len(sys.argv) > 1:
        global checkLatestRopFileSize
        arguments = sys.argv[1:]
        try:
            opts, args = getopt(arguments, 'h:c:m:s:', ['help', 'checkLatestRopFileSize=', 'master=', 'servers='])
        except GetoptError:
            help_message()

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                help_message()
            elif opt in ('-c', '--checkLatestRopFileSize' ):
                if not arg:
                    printStatement('ERROR', 'Argument value can not be empty for param ' + opt)
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                arg_value = arg.strip().upper()
                if arg_value not in ('YES', 'NO'):
                    help_message()
                if arg_value == 'YES':
                    checkLatestRopFileSize = True
            elif opt in ('-m', '--master' ):
                if not arg:
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                master_server = arg.strip()
            elif opt in ('-s', '--servers'):
                if not arg:
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                servers = arg.strip()
            else:
                help_message()
    
    if os.path.isdir(result_path):
        rmtree(result_path)
    os.makedirs(result_path, 0755)

    if not os.path.isfile(SIM_DATA_FILE):
        util.printStatements(SIM_DATA_FILE + ' is not present.', 'ERROR', True)

    updateFileSizeDict()
    collectSimDataContent()
    collectPlaybackSimData()
    if not SIM_CHAR_MAP:
        util.printStatements('No supported simulation found.', 'WARNING', True)

    gatherPmStatsData()
    writeDataAsPerStatistics()
    
    generateCsvReport()
    
    if master_server:
        if master_server == HOSTNAME:
            waitForOtherServersFile()
            printInformationInTabularFormat()
        else:
            global IP_ADDRESS
            IP_ADDRESS = socket.gethostbyname(master_server)
            doRemoteCopy()
    else:
        if sims_not_supported_list:
            util.printStatements('HOSTNAME : ' + HOSTNAME + ' these simulations are not supported with file size finder : ' + str(sims_not_supported_list), 'WARNING')
        printInformationInTabularFormat()
        if not entire_status:
            util.printStatements('HOSTNAME : ' + HOSTNAME + ' these simulations are not alligned with PM expected file size : ' + str(sims_not_aligned_list), 'WARNING')


if __name__ == '__main__':
    main()
