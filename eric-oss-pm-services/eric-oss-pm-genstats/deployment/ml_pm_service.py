#!/usr/bin/python

from time import time, strftime, sleep, localtime, gmtime
import os, logging, sys, json, copy
from _collections import defaultdict
from datetime import datetime
from multiprocessing import Pool, cpu_count
from utilityFunctions import Utility

# Creating Objects
util = Utility()

formatter = logging.Formatter('%(asctime)s : %(process)d : %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def setup_logger(name, log_file_name, level=logging.DEBUG):
    handler = logging.FileHandler(log_file_name)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

log_file = '/netsim_users/pms/logs/ml_pm_service.log'
norm_log = setup_logger('normal_logging', log_file)

instr_log_file = '/netsim_users/pms/logs/ml_pm_service_instrumentation.log'
instr_log = setup_logger('instrumentation_logging', instr_log_file)

precooked_folder, current_time, script_end_time = None, None, None
rop_file_format, req_file_deletion = None, True
timestamp_mapping, fileInformationMap, processed_node_map = defaultdict(list), defaultdict(list), defaultdict(list)
unique_timestamps_list_of_c_sample_for_new_reqt = []
timestamps_list_for_ml6352_c_file_one_day_rop_for_new_reqt = []
list_of_dictionaries_of_c_sample_for_new_reqt = []
ml_pm_path = '/c/pm_data/'
pms_path = '/pms_tmpfs/simulation_name/node_name' + ml_pm_path
request_location = '/netsim_users/pms/minilink_templates/minilink_requests/'
default_software_version = '2-8'
fifteen_min_in_sec, one_day_in_sec = 900, 86400
minilink_template_location = '/pms_tmpfs/xml_step/minilink_templates/'
filesToConsume = ['A_HEADER', 'C_HEADER', 'A_FOOTER', 'C_FOOTER', 'A_SAMPLE', 'C_SAMPLE']
templateValues = {'localDn=' : 'PT-0-0-0-0_ML6352_243', 'userLabel=' : 'ML6352_243', 'swVersion=' : 'CXP9026371_3_R10F110_2-8'}
file_writer_order = {'A' : ['A_HEADER', 'A_SAMPLE', 'A_FOOTER'], 'C' : [ 'C_HEADER', 'C_SAMPLE', 'C_FOOTER'],
                     'ML6352_NEW_A' : ['A_HEADER', 'A_NEW_SAMPLE', 'A_FOOTER'], 'ML6352_NEW_C' : ['C_NEW_HEADER', 'C_NEW_SAMPLE', 'C_NEW_FOOTER']}
ml_outdoor_special_map = {'ML6352_NEW_REQT' : {'A_SAMPLE' : 'Ml6352_New_Request_MiniLink_Outdoor_A_Sample_File.xml',
                                               'C_SAMPLE' : 'Ml6352_New_Request_MiniLink_Outdoor_C_Sample_File.xml'}}

def generateOffSetValue(t):
    offset, extra_seconds = util.generateOffSetValue(t)
    if offset is None:
       norm_log.error('Exception while calculating offset value.')
       clearRopInfoDict()
       sys.exit()
    else:
         return offset, extra_seconds

#type = False for C files,type = True for A files
def getTimeInIsoFormat(t, type=False):
    TimeInIsoFormat =  util.getTimeInIsoFormat(t, type)
    if TimeInIsoFormat is None:
       norm_log.error('Exception while creating time format.')
       clearRopInfoDict()
       sys.exit()
    else:
        return TimeInIsoFormat

def generateRopFolderLocation():
    global precooked_folder, script_end_time, current_time
    precook_template_location = '/pms_tmpfs/xml_step/minilink_templates/precook_templates/'
    if not os.path.isdir(precook_template_location):
        norm_log.error(precook_template_location + " location does not exists !!")
    global current_time
    current_time = (int(time()) / fifteen_min_in_sec) * fifteen_min_in_sec
    script_end_time = current_time + fifteen_min_in_sec
    ropFolder = getTimeInIsoFormat(script_end_time)
    precooked_folder = precook_template_location + ropFolder + '_OUTDOOR/'
    norm_log.info('Selected ROP for Minilink PM generation is : ' + ropFolder + '_OUTDOOR')


def clearRopInfoDict():
    global fileInformationMap
    try:
        if fileInformationMap:
            instr_log.info('Clearing cached data.')
            fileInformationMap.clear()
            if fileInformationMap:
                norm_log.error('Not able to clear cache information.')
                scriptTermination()
            else:
                instr_log.info('Cached data removed.')
    except Exception as x:
        stackTraceLogging('Exception while removing cached information.', str(x))


def consumeRopInformation():
    global fileInformationMap
    for fileType in filesToConsume:
        file_name = precooked_folder + fileType
        if os.path.isfile(file_name):
            fin = None
            try:
                fin = open(file_name, 'r')
                for line in fin:
                    fileInformationMap[fileType].append(line)
            except Exception as x:
                stackTraceLogging('Exception while reading precooked rop information of file ' + file_name, str(x))
                clearRopInfoDict()
            finally:
                fin.close()
        else:
            norm_log.error('File ' + file_name + ' not found.')
            scriptTermination()


def renameRequestFile(req):
    try:
        os.rename(req, req + '_processed')
    except Exception as x:
        stackTraceLogging('Exception while renaming the request file ' + req, str(x))
        clearRopInfoDict()


def getDestinationPath(sim, node):
    return pms_path.replace('simulation_name', sim).replace('node_name', node)


def convert_ipv6_address(ipAddress):
    elements = ipAddress.split('::')
    padding_needed = (8 - len(elements[0].split(':')) - len(elements[1].split(':'))) * 4
    newIpAddress = ''
    for i in elements[0].split(':'):
        newIpAddress += i.upper().zfill(4)
    if padding_needed > 0:
        newIpAddress = newIpAddress + str(0)*padding_needed
    for i in elements[1].split(':'):
        newIpAddress += i.upper().zfill(4)
    return newIpAddress


def generatePmFile(file_type, file_name, location, localdn, userlabel, sf_version, new_reqt, start = None):
    if new_reqt and file_type == 'C':
        start_rop = int(start)
        required_rop_list_from_request = unique_timestamps_list_of_c_sample_for_new_reqt[start_rop - 1:]
        header_time = current_time - one_day_in_sec + ((start_rop - 1)*fifteen_min_in_sec)
        header_iso = getTimeInIsoFormat(header_time)
        file_name = file_name.replace('<start_time>', header_iso).replace(':','_')
        fileInformationMap['C_NEW_HEADER'] = copy.copy(fileInformationMap['C_HEADER'])
        #The below line of code is for updating header time iso with the existing endTime value
        fileInformationMap['C_NEW_HEADER'][5] = fileInformationMap['C_NEW_HEADER'][5].replace(fileInformationMap['C_NEW_HEADER'][5].split('"')[1], header_iso)
    if new_reqt:       #File order handling for ml6352 new request support
        file_order = file_writer_order['ML6352_NEW_' + file_type]
    else:
        file_order = file_writer_order[file_type]
    pm_out = None
    try:
        pm_out = open(location + file_name, 'a+')
        update_header = True
        for order in file_order:
            if order == 'C_NEW_SAMPLE':
               #The content of the 'c' file will be taken from list of dictionaries
               for elem_dict in list_of_dictionaries_of_c_sample_for_new_reqt:
                   for key in elem_dict:
                       if key in required_rop_list_from_request:
                          line = elem_dict[key]
                          line = line.replace(key, timestamp_mapping[key])
                          pm_out.write(line)
            for line in fileInformationMap[order]:
                if update_header:
                    if 'localDn=' in line:
                        line = line.replace(templateValues['localDn='], localdn)
                    if 'userLabel=' in line :
                        line = line.replace(templateValues['userLabel='], userlabel)
                    if 'swVersion=' in line :
                        line = line.replace(templateValues['swVersion='], sf_version)
                pm_out.write(line)
            update_header = False
        pm_out.flush()
    except Exception as x:
        stackTraceLogging('Issue while writing file ' + file_name, str(x))
        clearRopInfoDict()
    finally:
        pm_out.close()


def stackTraceLogging(message, exc_message):
    norm_log.error(message)
    norm_log.error(exc_message)


def process_request(req):
    request_information = {}
    req_f, sim_name, node_name = None, None, None
    try:
        req_f = open(req, 'r')
        req_elements = req_f.readline().split('\n')[0].split(';')
        for element in req_elements:
            sub_elements = element.split('::', 1)
            if sub_elements[0] == 'softwareVersionRelease':
                if len(sub_elements) == 1:
                    request_information[sub_elements[0]] = default_software_version
                    continue
            request_information[sub_elements[0]] = sub_elements[1]
        sim_name = request_information['sim_name']
        node_name = request_information['node_name']
    except Exception as x:
        stackTraceLogging('Issue while reading request file ' + req, str(x))
        clearRopInfoDict()
    finally:
        req_f.close()
    dest_path = getDestinationPath(request_information['sim_name'], request_information['node_name'])
    if not os.path.isdir(dest_path):
        try:
            os.makedirs(dest_path, 0755)
        except Exception as x:
            stackTraceLogging('Issue while creating directory ' + dest_path, str(x))
            clearRopInfoDict()
    user_label = request_information['node_name']
    localDn = request_information['node_IP'].replace(':', '#').replace('.','-') + '_' + user_label
    ip_address = None
    if '.' not in request_information['node_IP']:
        ip_address = convert_ipv6_address(request_information['node_IP'])
    else:
        ip_address = request_information['node_IP'].replace('.', '-')
    a_rop_file_name = a_rop_file_format.replace('<FILE_TYPE>', 'A').replace('<IP_ADDRESS>', ip_address).replace('<USER_LABEL>', user_label).replace('<RC_ID>', request_information['rcID'])
    if 'new_request_1' in request_information:   #For ml6352 new request support
       if request_information['interval_min'] != '1440':
          c_rop_file_name = ml6352_c_rop_file_format.replace('<FILE_TYPE>', 'C').replace('<IP_ADDRESS>', ip_address).replace('<USER_LABEL>', user_label).replace('<RC_ID>', request_information['rcID'])
          generatePmFile('C', c_rop_file_name, dest_path, localDn, user_label, request_information['softwareVersionRelease'], True, request_information['start_interval'])
       else:
          generatePmFile('A', a_rop_file_name, dest_path, localDn, user_label, request_information['softwareVersionRelease'], True)
    else:
       c_rop_file_name = c_rop_file_format.replace('<FILE_TYPE>', 'C').replace('<IP_ADDRESS>', ip_address).replace('<USER_LABEL>', user_label).replace('<RC_ID>', request_information['rcID'])
       generatePmFile('A', a_rop_file_name, dest_path, localDn, user_label, request_information['softwareVersionRelease'], False)
       generatePmFile('C', c_rop_file_name, dest_path, localDn, user_label, request_information['softwareVersionRelease'], False)
    request_information.clear()
    renameRequestFile(req)
    return sim_name, node_name


def processFeedBackInformation(result):
    global processed_node_map
    processed_node_map[result[0]].append(result[1])


def initiateRequestPool(reqs):
    #req_pool = Pool(int(cpu_count()/2))
    req_pool = Pool(1)
    for r in reqs:
        req_pool.apply_async(process_request, args=(r,), callback=processFeedBackInformation)
    req_pool.close()
    req_pool.join()


def fetchAppropriateRequestFile():
    filtered_req_list = []
    for x in filter(None, os.listdir(request_location)):
        if '_process' not in x:
            req_final_path = request_location + x
            if os.path.getmtime(req_final_path) >= current_time:
                filtered_req_list.append(req_final_path)
    return filtered_req_list


def fetchMiniLinkRequests():
    global processed_node_map
    status = False
    requests = fetchAppropriateRequestFile()
    request_count = len(requests)
    if request_count == 0:
        return status
    else:
        status = True
        norm_log.info('MiniLink request(s) found and processing.')
        instr_log.info('Number of MiniLink request found is : ' + str(request_count))
        if request_count <= 3:
            for r in requests:
                sim, node = process_request(r)
                processed_node_map[sim].append(node)
        else:
            initiateRequestPool(requests)
        norm_log.info('MiniLink request(s) has been processed, searching for new request(s).')
        instr_log.info('Number of MiniLink request processed is : ' + str(request_count))
        instr_log.info('Processed node list : ' + json.dumps(processed_node_map) + '.')
    if processed_node_map:
        processed_node_map.clear()
    return status


def scriptTermination():
    norm_log.info('Terminating Minilink PM service.')
    sys.exit()


def generateRopFileNameFormat():
    global a_rop_file_format
    global c_rop_file_format
    global localMidnight
    global ml6352_c_rop_file_format
    offset, extra_seconds = generateOffSetValue(time())
    localMidnight = util.localMidnight(offset, extra_seconds, current_time - one_day_in_sec, one_day_in_sec)
    c_rop_file_format = '<FILE_TYPE>' + getTimeInIsoFormat(script_end_time - one_day_in_sec).replace(':', '_') + '-' + \
                        getTimeInIsoFormat(script_end_time).replace(':','_') + \
                        '-PT-' + '<IP_ADDRESS>' + '_' + '<USER_LABEL>' + '_-_' + '<RC_ID>' + '.xml'

    a_rop_file_format = '<FILE_TYPE>' + getTimeInIsoFormat(localMidnight , type=True).replace(':', '_') + '-' + \
                        getTimeInIsoFormat(localMidnight + (2 * one_day_in_sec), type=True).replace(':','_') + \
                        '-PT-' + '<IP_ADDRESS>' + '_' + '<USER_LABEL>' + '_-_' + '<RC_ID>' + '.xml'

    #File format of 'c' file for ml6352 new request support
    ml6352_c_rop_file_format = '<FILE_TYPE>' + '<start_time>' + '-' + getTimeInIsoFormat(current_time).replace(':','_')  + \
                        '-PT-' + '<IP_ADDRESS>' + '_' + '<USER_LABEL>' + '_-_' + '<RC_ID>' + '.xml'

def removeAllProcessedRequestFile():
    for x in filter(None, os.listdir(request_location)):
        if x.endswith('_processed'):
            try:
                os.remove(request_location + x)
            except Exception as e:
                stackTraceLogging('Exception while renaming the request file ' + request_location + x, str(e))


def iterateOnDirectoryForRequests():
    while (time() < script_end_time):
        found_status = fetchMiniLinkRequests()
        if not found_status:
            sleep(1)
    clearRopInfoDict()
    if req_file_deletion:
        removeAllProcessedRequestFile()


def createRequestLocation():
    if not os.path.isdir(request_location):
        try:
            os.makedirs(request_location, 0755)
        except Exception as x:
            stackTraceLogging('Problem while creating ' + request_location, str(x))
            clearRopInfoDict()

#The below method will consume Data for A sample for ml6352 new requirement
def consumeDataForASampleForMl6352NewRequirement():
    ml6352_new_a_sample = os.path.join(minilink_template_location, ml_outdoor_special_map['ML6352_NEW_REQT']['A_SAMPLE'])
    temp_epoch = localMidnight + one_day_in_sec
    with open(ml6352_new_a_sample, 'r') as s_fin:
        for line in s_fin:
            if "endTime=" in line:
               tempIso = getTimeInIsoFormat(temp_epoch, type=True)
               line = line.replace('2021-03-18T08:30:00+00:00', tempIso)
               temp_epoch += one_day_in_sec
            fileInformationMap['A_NEW_SAMPLE'].append(line)

#The Below method will consume date data from ml652 new c sample in to list of dictionaries,a sample in to fileInformationMap
def consumeDataForMl6352NewRequirement():
    global unique_timestamps_list_of_c_sample_for_new_reqt, list_of_dictionaries_of_c_sample_for_new_reqt, fileInformationMap
    #consuming 'C' sample file for ml6352 new requirement
    ml6352_new_c_sample = os.path.join(minilink_template_location, ml_outdoor_special_map['ML6352_NEW_REQT']['C_SAMPLE'])
    with open(ml6352_new_c_sample, 'r') as s_fin:
       single_instance_list = []
       interval_endTime = None
       for line in s_fin:
           if "</measInfo>" in line:
              single_instance_list.append(line)
              list_of_dictionaries_of_c_sample_for_new_reqt.append({interval_endTime:''.join(single_instance_list)})
              single_instance_list = []
           elif "endTime=" in line:
              interval_endTime=line.split('"')[3]
              #The below list will contain all 96 unique time stamps of input 'c' sample
              if interval_endTime not in unique_timestamps_list_of_c_sample_for_new_reqt:
                 unique_timestamps_list_of_c_sample_for_new_reqt.append(interval_endTime)
              single_instance_list.append(line)
           else:
              single_instance_list.append(line)
    #Updating footer timestamp for ml6352 new requirement for c file
    fileInformationMap['C_NEW_FOOTER'] = copy.copy(fileInformationMap['C_FOOTER'])
    temp_time = fileInformationMap['C_NEW_FOOTER'][2].split('"')[1]
    fileInformationMap['C_NEW_FOOTER'][2] = fileInformationMap['C_NEW_FOOTER'][2].replace(temp_time, getTimeInIsoFormat(current_time))
    consumeDataForASampleForMl6352NewRequirement()

def generateTimeStampListForOneDayRopCFileMl6352():
    #The below list contains all the 96 time stamps for ml6352 new reqt c file basing on the script invocation time
    global timestamps_list_for_ml6352_c_file_one_day_rop_for_new_reqt
    start_end_time_for_c_sample = current_time - one_day_in_sec + fifteen_min_in_sec
    for i in range(0,96):
        timestamps_list_for_ml6352_c_file_one_day_rop_for_new_reqt.append(getTimeInIsoFormat(start_end_time_for_c_sample + (i * fifteen_min_in_sec)))

#The below method created time stamp mapping of unique timestamp of input c sample file and one day rops for c file ml6352 new requirement
def createTimeStampMappingForCFileMl6352NewRequirement():
    global timestamp_mapping
    timestamp_mapping = dict(zip(unique_timestamps_list_of_c_sample_for_new_reqt, timestamps_list_for_ml6352_c_file_one_day_rop_for_new_reqt))

def main():
    norm_log.info('MiniLink PM service started.')
    generateRopFolderLocation()
    if os.path.isdir(precooked_folder):
        norm_log.info('Reading pre-cooked template information.')
        consumeRopInformation()
        norm_log.info('Pre-cooked template information reading completed.')
        generateRopFileNameFormat()
        #The below function will be used for ml6352 c file new requirement for generating timestamps
        generateTimeStampListForOneDayRopCFileMl6352()
        consumeDataForMl6352NewRequirement()
        createTimeStampMappingForCFileMl6352NewRequirement()
        createRequestLocation()
        iterateOnDirectoryForRequests()
    else:
        norm_log.error('ROP Folder ' + precooked_folder + ' does not exist.')
    scriptTermination()


if __name__ == '__main__':
    main()


