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

#############################################################################
# Version no    :  NSS 22.12
# Purpose       :  Has various generic utility methods.
# Jira No       :  NSS-35445
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/12904520/
# Description   :  Adding code changes to take 1st started node info and default pm paths
# Date          :  19/07/2022
# Last Modified :  surendra.mattaparthi@tcs.com
###############################################################################

from datetime import datetime
from datetime import datetime as d
import os, sys, errno, json, traceback
from shutil import copyfile, rmtree
from socket import gethostname
from subprocess import Popen, PIPE, check_output
from time import time, strftime, sleep, localtime, gmtime
import errno

class Utility:

    """ default_pm_path (dict) = { "node_type" : "default_pm_path_for_events" } """
    default_event_pm_path = { 'FIVEGRADIONODE' : '/rcs/sftp', 'GNODEBRADIO' : '/pm_data_'}

    """ JSON file for configurable celltrace """
    celltrace_json = '/netsim_users/pms/etc/.celltrace_info.json'

    """ TEXT file for Selective Node Information """
    selective_ne_conf = '/netsim_users/pms/etc/.selective_ne_conf'

    """ cell trace file location/directory """
    celltrace_file_location = '/netsim_users/pms/rec_templates/'

    """ sim_data.txt file """
    sim_data_file = '/netsim/genstats/tmp/sim_data.txt'

    """ sim_info.txt file """
    sim_info_file = '/netsim/genstats/tmp/sim_info.txt'

    """ Parameter name of multiprocess instance from nestim_cfg """
    multiProcess_param = 'STATS_MAX_CONCURRENT'

    """ started node information file """
    startedNodeInfoFile = '/tmp/showstartednodes.txt'

    """ netsim_cfg file """
    netsim_cfg = '/netsim/netsim_cfg'

    """ netsim shell script """
    netsim_script = '/netsim/inst/netsim_shell'

    """ db_dir path """
    netsim_dbdir = '/netsim/netsim_dbdir/simdir/netsim/netsimdir/'

    """ mounting script """
    mount_script = '/netsim_users/pms/bin/createTempFsMountForNodes.sh'

    nr_count = 0

    """ Mapping of node type wuth File format and extension """
    events_file_format_mapping = {'FIVEGRADIONODE' : { 'CELLTRACE' : ['A<START_DATE>.<START_TIME>-<END_TIME>_CellTrace_<EventProducer><FILE_ID>.gpb', '.gz']},
                                  'GNODEBRADIO' : { 'CELLTRACE' : ['A<START_DATE>.<START_TIME>-<END_TIME>_CellTrace_SubNetwork=5G,SubNetwork=Ireland,MeContext=<NODE>,ManagedElement=<NODE>_<EventProducer><FILE_ID>.gpb', '.gz']}}


    """ Mapping of FIVEG Nodes celltrace files """
    ne_to_events_file ={1: {'FIVEGRADIONODE' : {'low' : {'CUCP' : 'celltrace_2304K.bin.gz',
                                                  'CUUP' : 'celltrace_2304K.bin.gz',
                                                    'DU' : 'celltrace_2304K.bin.gz',
                                                     'default' : 'celltrace_2304K.bin.gz'},
                                         'high' : {'CUCP' : 'celltrace_768K.bin.gz',
                                                    'CUUP' : 'celltrace_768K.bin.gz',
                                                     'DU' : 'celltrace_768K.bin.gz',
                                                     'default' : 'celltrace_768K.bin.gz'}},
                     'GNODEBRADIO' : {'low' : {'CUCP': 'celltrace_cucp_761K.bin.gz',
                                               'CUUP': 'celltrace_cuup_764K.bin.gz',
                                               'DU': 'celltrace_du_767K.bin.gz',
                                               'default' : 'celltrace_2304K.bin.gz'},
                                       'high' : {'CUCP' : 'celltrace_256k.bin.gz',
                                                  'CUUP' : 'celltrace_256k.bin.gz',
                                                   'DU' : 'celltrace_256k.bin.gz',
                                                   'default' : 'celltrace_768K.bin.gz'}}},
                     2: {'GNODEBRADIO' : {'low' : {'CUCP' : 'celltrace_cucp_1MB.bin.gz',
                                                  'CUUP' : 'celltrace_cuup_1MB.bin.gz',
                                                    'DU' : 'celltrace_du_1MB.bin.gz',
                                                     'default' : 'celltrace_1MB.bin.gz'},
                                            'high' : {'CUCP' : 'celltrace_cucp_333KB.bin.gz',
                                                    'CUUP' : 'celltrace_cuup_333KB.bin.gz',
                                                     'DU' : 'celltrace_du_333KB.bin.gz',
                                                     'default' : 'celltrace_333KB.bin.gz'}},
                        'FIVEGRADIONODE' : {'low' : {'CUCP': 'celltrace_cucp_2304K.bin.gz',
                                               'CUUP': 'celltrace_cuup_2304K.bin.gz',
                                               'DU': 'celltrace_du_2304K.bin.gz',
                                               'default' : 'celltrace_768K.bin.gz'},
                                       'high' : {'CUCP' : 'celltrace_cucp_768k.bin.gz',
                                                  'CUUP' : 'celltrace_cuup_768k.bin.gz',
                                                   'DU' : 'celltrace_du_768k.bin.gz',
                                                   'default' : 'celltrace_768K.bin.gz'}}}}



    def copyWithOutDirectoryChecking(self, src, dest):
        """ Function will do blind copy """
        try:
            copyfile(src, dest)
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.printStatements('Directory ' + os.path.dirname(dest) + ' not present.', 'ERROR')
            else:
                raise e


    def getCellCount(self, node_name):
        nr_cell_data_file = '/netsim_users/pms/etc/nr_cell_data.txt'
        count = 0
        node_check = 0
        with open(nr_cell_data_file, 'r') as inFile:
             for line in inFile:
                 if line.startswith('ManagedElement=') and node_name in line:
                     cell_info = line.split(',')[-1].split('=')
                     cell_mo, node_cell_info  = cell_info[0],cell_info[1].split('-')
                     if cell_mo == 'NRCellCU' and node_name == node_cell_info[0]:
                        count += 1
                        node_check = 1
                 else:
                     if node_check == 1:
                        return count

    def mountDirectory(self, src_path, dest_path):
        """ Will call the script which will mount the path """
        try:
            dest_path = [x for x in filter(None, dest_path.split('/'))]
            dest_path.insert(7, 'fs')
            os.system('echo shroot | su root -c "' + self.mount_script + ' ' + src_path + ' /' + '/'.join(dest_path) + '"')
        except:
            traceback.print_exc()

    def linkFileSourceToDest(self, srcFile, destFile, dirPermission=0o755):
        try:
            if not os.path.isdir(os.path.dirname(destFile)):
                os.makedirs(os.path.dirname(destFile), dirPermission)
            os.symlink(srcFile, destFile)
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                traceback.print_exc()
        except:
            traceback.print_exc()

    def copyFileSourceToDest(self, srcFile, destFile, isForcedDirectoryCreation, dirPermission):
        """ Method copy files to source to destination and create directory if not exist for source """
        try:
            if isForcedDirectoryCreation:
                if not os.path.isdir(os.path.dirname(destFile)):
                    os.makedirs(os.path.dirname(destFile), dirPermission)
                    #if not destFile.startswith(self.netsim_dbdir):
                    #    self.mountDirectory(os.path.dirname(destFile), os.path.dirname(destFile).replace('/pms_tmpfs/', self.netsim_dbdir))
                    self.copyWithOutDirectoryChecking(srcFile, destFile)
                else:
                    self.copyWithOutDirectoryChecking(srcFile, destFile)
            else:
                self.copyWithOutDirectoryChecking(srcFile, destFile)
        except:
            traceback.print_exc()


    def createRecursiveDirectory(self, inputPath):
        os.makedirs(inputPath)


    def giveUserPermission(self, user, path, recursive=False):
        if recursive:
            self.run_shell_command('chown -R ' + user + ':' + user + ' ' + path)
        else:
            self.run_shell_command('chown ' + user + ':' + user + ' ' + path)


    def giveReadWritePermission(self, mode, path, recursive=False):
        if recursive:
            self.run_shell_command('chmod -R ' + mode + ' ' + path)
        else:
            self.run_shell_command('chmod ' + mode + ' ' + path)


    def writeSimpleDataInFile(self, fileWithPath, data):
        """ This method write single line data """
        fout = ''
        try:
            if self.checkDirectoryExistance(os.path.dirname(fileWithPath)):
                fout = open(fileWithPath, 'w')
                fout.write(data)
                fout.flush()
            else:
                self.printStatements('Directory ' + os.path.dirname(fileWithPath) + ' not exists. Can not write file ' + os.path.basename(fileWithPath), 'ERROR')
        except:
            traceback.print_exc()
        finally:
            fout.close()


    def get_value_from_netsim_cfg(self, param):
        with open(self.netsim_cfg) as f:
            for line in f:
                if line.startswith(param):
                    return line.strip().replace('\n', '').replace('"', '').split('=')[-1]
        return None


    def getSpecificNratNodeInformtion(self):
        name, file = None, None
        with open(self.netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith('NRAT_CELLTRACE_30MB_FILE='):
                    file = line.strip().split('"')[1]
                elif line.startswith('NRAT_CELLTRACE_30MB_NODE='):
                    name = line.strip().split('"')[1]
                if name and file:
                    return True, name, file
        self.printStatements('Information related to specific NRAT node not found in netsim_cfg.', 'WARNING')
        return False, None, None


    def getRequiredCounterVolumeInformation(self):
        with open(self.netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith('REQUIRED_COUNTER_VOLUME='):
                    return line.strip().split('"')[1].strip()
        self.printStatements('Unable to find required counter volume information in netsim_cfg.', 'ERROR', True)


    def getDeploymentVersionInformation(self, inputFile=''):
        file = self.netsim_cfg
        if inputFile:
            file = '/tmp/' + inputFile
        with open(file, 'r') as f:
            for line in f:
                if line.startswith('TYPE='):
                    return line.strip().split('"')[1].strip()
        self.printStatements('Unable to find deployment version information in ' + file + '.', 'ERROR', True)


    def createManifestFile(self, manifest_map):
        """ This method will create the manifest files """
        try:
            manifest_format = manifest_map[next(iter(manifest_map))][0].split('_')[0] + '_Trace.manifest'
            for directory, fileList in manifest_map.items():
                self.writeSimpleDataInFile(directory + manifest_format, '\n'.join(fileList) + '\n')
        except:
            traceback.print_exc()


    def getSimListFromNetsimCfg(self, list_string):
        """ return the sim list based on provided input of list or mme_list from netsim_cfg """
        searchString = list_string
        with open(self.netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith(searchString):
                    return [x for x in filter(None, line.split('"')[1].split())]
        self.printStatements(searchString + ' is not present in ' + self.netsim_cfg + ' file.', 'ERROR', True)

    def get_netsim_cfg_value(self, value):
        with open(self.netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith(value):
                    return [x for x in filter(None, line.split('"')[1])]

    def getNrCtrCount(self):
        with open(self.netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith("NR_CTR_FILES"):
                    return [x for x in filter(None, line.split('=')[1])]
        return None

    def filterNodePathListFromStartedNodeFile(self, input_node_path_list):
        """ This method filter the node path list based on started node information """
        outList = []
        startedFile = ''
        try:
            startedFile = open(self.startedNodeInfoFile, 'r')
            for node_path in input_node_path_list:
                startedFile.seek(0, 0)
                node_name = node_path.split("/")[-2].strip()
                if node_name:
                    for line in startedFile:
                        if node_name.split("=")[-1] in [x for x in filter(None, line.split())]:
                            if "<CTR>" in line:
                                outList.append(node_path)
                                break
        except:
            traceback.print_exc()
        finally:
            startedFile.close()
        return outList


    def reCorrectPmPath(self, path):
        """ Correct the path """
        try:
            if not path.startswith('/'):
                return '/' + path
            return path
        except:
            traceback.print_exc()


    def getJsonMapObjectFromFile(self, inputFile):
        """ This method return json object of file data """
        jsonObject = ''
        if self.checkFileExistance(inputFile):
            inF = open(inputFile, 'r')
            jsonObject = json.load(inF)
        else:
            self.printStatements(inputFile + ' not present.', 'ERROR', True)
        return jsonObject


    def getEnrichedJsonDataFromKey(self, jsonMap, inputKey):
        """ This method return values associated with given Json key from Json map object. """
        try:
            if not jsonMap:
                return False, 'False'
            if inputKey in jsonMap:
                return True, jsonMap[inputKey]
            else:
                return False, []
        except:
            traceback.print_exc()


    def validateStringForBoolCheck(self, inString):
        """ Check string for boolean True/False comperision """
        try:
            if inString.lower() == 'true':
                return True
            return False
        except:
            traceback.print_exc()


    def isOffsetRequired(self, sim_name, node_type):
        """ This method send True or False for offset required in PM file name
            or not based on sim name and node type
        """
        if node_type == 'FIVEGRADIONODE' or node_type == '5GRADIONODE':
            return False
        return True


    def getHostName(self):
        """ This method return host name or server name on which it is executing
        """
        hostID = gethostname()
        if hostID.startswith('atvts') or os.path.exists('/netsim/genstats/.dockerenv'):
            return 'netsim'
        return hostID


    def removeFilesIfExists(self, fileWithPath):
        """ This method blindly tries to remove/delete file from given full file path,
            if file exists, delete the file - if file not exists then raise exception and check with
            file not found exception if not matching then raise exception.
        """
        try:
            os.remove(fileWithPath)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise


    def removeDirectoryIfExists(self, dirPath):
        """ This method blindly delete the directory is exists.
        """
        if self.checkDirectoryExistance(dirPath):
            rmtree(dirPath)


    def getBasename(self, fileWithPath):
        """ This method returns basename of filepath """
        return os.path.basename(fileWithPath)


    def writeJsonFileFromInputMap(self, inMap, inFile):
        """ This method will write dictionary data in to a JSON file """
        with open(inFile, 'w') as f:
            json.dump(inMap, f)


    def getPmsPathForSim(self, sim_name, node_type):
        """ This method return pms path based on sim and node type
        """
        try:
            if node_type == 'SGSN':
                return '/netsim/netsim_dbdir/simdir/netsim/netsimdir/'
            return '/ericsson/pmic/CELLTRACE/'
        except:
            traceback.print_exc()


    def getherNodeList(self, pms_path, sim_name, epoch_rop_dir=''):
        try:
            my_node_list = []
            nr_topology_file = '/netsim_users/pms/etc/nr_cell_data.txt'
            sim_id = sim_name.split('-')[-1]
            with open(nr_topology_file) as topo:
                for line in topo:
                    fdn_name = line.split('=')[-1].split('-')[0]
                    if fdn_name.startswith(sim_id + 'gNodeBRadio'):
                        my_node_list.append(fdn_name)
                my_node_list = list(set(my_node_list))
            return [pms_path + 'SubNetwork=Europe,SubNetwork=Ireland,MeContext=' + node + '/' + epoch_rop_dir for node in my_node_list]
        except:
            traceback.print_exc()


    def checkForNodeStatus(self, inputNode, inputFile):
        """ This method return True or False based on node is started or not
        """
        startedNode, f = False, ''
        try:
            f = open(inputFile, 'r')
            for line in f:
                if inputNode in [x for x in filter(None, line.split())]:
                    startedNode = True
                    break
        except:
            traceback.print_exc()
        finally:
            f.close()
        return startedNode


    def run_shell_command(self, inputCommand):
        """ This is the generic method, Which spawn a new shell process to get the job done
        """
        try:
            output = Popen(inputCommand, stdout=PIPE, shell=True).communicate()[0]
            return output
        except:
            traceback.print_exc()


    def getCurrentDateTime(self):
        """ Creates date time in formatted way for logging.
        """
        return d.now().strftime('%Y-%m-%d %H:%M:%S')


    def printStatements(self, message, msgType, exitStatus=False):
        """ Prints message on console and Terminate the process in case of ERROR message
        """
        print (self.getCurrentDateTime() + ' ' + msgType + ' : ' + str(message))
        if exitStatus:
            sys.exit(1)


    def getActualMpInstance(self):
        """ This method manages multiprocess instance
        """
        if not self.checkFileExistance(self.netsim_cfg):
            self.printStatements(self.netsim_cfg + ' file not present.', 'ERROR', True)
        with open(self.netsim_cfg, 'r') as f:
            mp_pool_size = ''
            for line in f:
                if line.startswith(self.multiProcess_param):
                    mp_pool_size = line.split('=')[1].strip()
                    break
            if mp_pool_size and mp_pool_size.isdigit() and int(mp_pool_size) > 1:
                return int(mp_pool_size)
        return 1


    def fetchNodeTypeInformation(self, inputSim):
        sim_info_obj = None
        try:
            sim_info_obj = open(self.sim_info_file, 'r')
            for line in sim_info_obj:
                line = line.replace('\n', '').strip().split(':')
                if line[0] == inputSim:
                    return line[1].strip(), True
            self.printStatements('Simulation not found in ' + self.sim_info_file, 'WARNING')
            return None, False
        except Exception as x:
            self.printStatements('Exception while fetching node type information from ' + self.sim_info_file + ' file.', 'ERROR')
            print (x)
        finally:
            sim_info_obj.close()


    def checkFileExistance(self, inputFile):
        """ Return True if file present
        """
        try:
            if os.path.isfile(inputFile):
                return True
            return False
        except:
            traceback.print_exc()


    def checkDirectoryExistance(self, inputPath):
        """ Return True if directory present
        """
        try:
            if os.path.isdir(inputPath):
                return True
            return False
        except:
            traceback.print_exc()


    def fetchNeList(self, inputPath):
        if self.checkDirectoryExistance(inputPath):
            return [ folder_list for folder_list in [x for x in filter(None, os.listdir(inputPath))] ]
        else:
            return []


    def localMidnight(self, offset, extra_seconds, time, one_day_sec):
        """ Return the epoch time of local Midnight """
        if offset[0] == '+':
           localMidnightvalue = ((time + extra_seconds) // one_day_sec) * one_day_sec
        else:
           localMidnightvalue = ((time - extra_seconds) // one_day_sec) * one_day_sec
        return localMidnightvalue

    def generateOffSetValue(self, t):
        """ Return the offset value of given epoch time and extra seconds """
        try :
             one_day_in_sec = 86400
             local_time, utc_time = datetime.fromtimestamp(t), datetime.utcfromtimestamp(t)
             extra_days, extra_seconds = (local_time - utc_time).days, (local_time - utc_time).seconds
             if extra_days == 0:
                if extra_seconds == 0:
                    return '+00:00', extra_seconds
                else:
                    return '+' + strftime('%H:%M', gmtime(extra_seconds)), extra_seconds
             elif extra_days == -1:
                  extra_seconds = (one_day_in_sec - extra_seconds)
                  return '-' + strftime('%H:%M', gmtime(extra_seconds)), extra_seconds
        except Exception as x:
            return None, None

    def getTimeInIsoFormat(self, t, type=False):
        """ Return the given epoch time in Iso Format"""
        try :
             if t >= 0:
                if type == True:
                   return strftime('%Y-%m-%dT%H:%M:%S', gmtime(t)) + self.generateOffSetValue(t)[0]
                else:
                   return strftime('%Y-%m-%dT%H:%M:%S', localtime(t)) + self.generateOffSetValue(t)[0]
             else:
                if type == True:
                   return (datetime.utcfromtimestamp(t)).strftime('%Y-%m-%dT%H:%M:%S') + self.generateOffSetValue(t)[0]
                else:
                   return (datetime.fromtimestamp(t)).strftime('%Y-%m-%dT%H:%M:%S') + self.generateOffSetValue(t)[0]
        except Exception as x:
            return None

    def getDeploymentType(self):
        depl_type = None
        try:
            with open(self.netsim_cfg, 'r') as f:
                for line in f:
                    if line.startswith('TYPE='):
                        depl_type = line.split("=")[1].rstrip()
                        break
        finally:
            f.close()
        return depl_type
