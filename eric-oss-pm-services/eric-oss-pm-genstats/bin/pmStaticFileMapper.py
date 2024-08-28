#!/usr/bin/python -u

'''
Created on August 14th, 2023

@author: xmanabh
'''
import gzip
import json
import os.path
import sys
from collections import defaultdict
from datetime import datetime

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
measValue = '<measValue measObjLdn='
NETSIM_CFG = '/netsim/netsim_cfg'
EBSN_METADATA_PATH = '/netsim_users/pms/etc/'
EBSN_TOPOLOGY_PATH = '/netsim_users/pms/etc/nr_ebsn_cell_data.txt'

PARAM_VALUES_TO_FETCH = {'EBSN_ESOA_PERFORMANCE': ['REPLAY_ENABLED', 'EBSN_PERFORMANCE_ENABLED']}

EBSN_SOURCE_PATH = None


def log_statement(msg, exit_value=None):
    print(get_current_date_time() + msg)
    if exit_value is not None:
        sys.exit(exit_value)


def get_current_date_time():
    return datetime.now().strftime(LOG_TIME_FORMAT) + ' '


def collect_use_case_info_from_netsim_cfg():
    if not os.path.exists(NETSIM_CFG) or not os.path.isfile(NETSIM_CFG):
        log_statement('ERROR : File {} does not exists or not a file.'.format(NETSIM_CFG), 1)
    log_statement('INFO : Collecting mapping use case(s) for replay...')
    use_cases_list = []
    with open(NETSIM_CFG, 'r') as cfg:
        for use_case, param_list in PARAM_VALUES_TO_FETCH.items():
            use_case_res_list = []
            for line in cfg:
                if line.split('=')[0] in param_list:
                    if line.strip().split('=')[1].replace(' ', '').upper() in ['YES', 'TRUE']:
                        use_case_res_list.append(True)
                    else:
                        use_case_res_list.append(False)
            if len(use_case_res_list) > 0 and len(use_case_res_list) == len(param_list):
                if False not in use_case_res_list:
                    use_cases_list.append(use_case)
    return use_cases_list


def get_rop_name(file, ne_type=None):
    if ne_type is None:
        '''
            This is default for STATS (LTE, NR, EBSN)
            File name : A20220621.1400+0200-1415+0200_SubNetwork=RAN,MeContext=NR99gNodeBRadio00031...
            Result : 20220621.1400
        '''
        return file[1:14]
    return None


def check_file_compliance(file_name, type_name, ext_list):
    for ext in ext_list:
        if file_name.startswith(type_name) and file_name.endswith(ext):
            return True
    return False


def get_full_fdn(file_name):
    '''
        This will fetch "SubNetwork=Europe,SubNetwork=Ireland,MeContext=NR01gNodeBRadio00001,ManagedElement=NR01gNodeBRadio00001"
    '''
    return file_name.split('_')[1].replace(' ', '').strip()


def get_files(source_dir):
    file_list = []
    for dir_path in [x for x in filter(None, source_dir.split(':'))]:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for f in [x for x in filter(None, os.listdir(dir_path))]:
                file_list.append(f)
    if len(file_list) > 0:
        return file_list
    else:
        log_statement('ERROR : No source files found.', 1)


def collect_rop_information_for_ebsn():
    log_statement('INFO : Collecting source replay rop information...')
    rop_info_map = defaultdict(lambda: defaultdict(list))
    fetched_files = get_files(EBSN_SOURCE_PATH)
    for replay_file in fetched_files:
        if check_file_compliance(replay_file, 'A', ['.xml.gz', '.xml']):
            full_fdn, rop_time = get_full_fdn(replay_file), get_rop_name(replay_file)
            if full_fdn is not None and full_fdn != '':
                if rop_time is not None and rop_time != '':
                    rop_info_map[rop_time][full_fdn].append(replay_file)
    log_statement('INFO : Source replay rop information collected.')
    if len(rop_info_map.keys()) > 0:
        log_statement('INFO : Total replay rop found : {}'.format(rop_info_map.keys()))
    else:
        log_statement('WARNING : No replay rop information found. Exiting process.', 1)
    return rop_info_map


def parse_nr_ebsn_topology_information():
    ebsn_topo_map = {}
    if os.path.exists(EBSN_TOPOLOGY_PATH) and os.path.isfile(EBSN_TOPOLOGY_PATH):
        log_statement('INFO : Parsing ebsn topology information.')
        with open(EBSN_TOPOLOGY_PATH, 'r') as ebsn_topo:
            for line in ebsn_topo:
                if 'NRCellCU=' not in line:
                    continue
                ne_name = line.strip().replace('\n', '').split('=')[-1].split('-')[0]
                if ne_name not in ebsn_topo_map:
                    ebsn_topo_map[ne_name] = 1
                else:
                    ebsn_topo_map[ne_name] = (ebsn_topo_map[ne_name] + 1)
        if len(ebsn_topo_map.keys()) == 0:
            log_statement('WARNING : No ebsn topology information found in {} file.'.format(EBSN_TOPOLOGY_PATH))
            log_statement('WARNING : Exiting process.', 1)
        log_statement('INFO : Ebsn topology information parsed successfully.')
    else:
        log_statement('ERROR : Either file {} does not exists or not a file.'.format(EBSN_TOPOLOGY_PATH), 1)
    return ebsn_topo_map


def get_count(file_obj, str):
    cell_count = 0
    for line in file_obj:
        if measValue in line and line.split(',')[-1].startswith(str):
            cell_count += 1
    return cell_count


def get_ebsn_compressed_file_data(file_path, search_string):
    file_data = None
    try:
        file_data = gzip.open(file_path, 'r')
        return get_count(file_data, search_string)
    except Exception as e:
        log_statement('ERROR : Issue while processing file {}.'.format(file_path), 1)
    finally:
        if file_data is not None:
            file_data.close()


def get_ebsn_uncompressed_file_data(file_path, search_string):
    try:
        with open(file_path, 'r') as file_data:
            return get_count(file_data, search_string)
    except Exception as e:
        log_statement('ERROR : Issue while processing file {}.'.format(file_path), 1)


def parse_cell_info_from_ebsn_input_source(fdn_to_files):
    processed_fdn_list, fdn_to_cell_map = [], defaultdict(list)
    log_statement('INFO : Parsing EBSN Replay input source.')
    for fdn_name, file_list in fdn_to_files.items():
        for file_name in file_list:
            if fdn_name in processed_fdn_list:
                break
            for network_element in ['_CUCP_', '_DU_']:
                if network_element not in file_name:
                    continue
                else:
                    search_str = 'NRCell' + network_element.replace('_', '').replace('CP', '') + '='
                    full_file_path = EBSN_SOURCE_PATH + file_name
                    if len(EBSN_SOURCE_PATH.split(':')) > 1:
                        for parent_dir in EBSN_SOURCE_PATH.split(':'):
                            if network_element.replace('_', '') in parent_dir:
                                full_file_path = parent_dir + file_name
                                break
                    cell_count = None
                    if file_name.endswith('.xml'):
                        cell_count = get_ebsn_uncompressed_file_data(full_file_path, search_str)
                    else:
                        cell_count = get_ebsn_compressed_file_data(full_file_path, search_str)
                    if cell_count is None:
                        log_statement(
                            'ERROR : Issue while fetching cell count info from {} file.'.format(full_file_path), 1)
                    fdn_to_cell_map[cell_count].append(fdn_name)
                    processed_fdn_list.append(fdn_name)
                    break
    log_statement('INFO : Parsing of EBSN Replay input completed.')
    return fdn_to_cell_map


def mapping_ebsn_topology_to_source_fdn(src_map, topo_map):
    final_fdn_map = {}  # map = { topology_fdn : source_fdn }
    for topo_ne_name, topo_ne_cell_cnt in topo_map.items():
        if topo_ne_cell_cnt not in src_map.keys():
            log_statement('ERROR : Input source does not have fdn with cell count {}.'.format(topo_ne_cell_cnt), 1)
        final_fdn_map[topo_ne_name] = src_map[topo_ne_cell_cnt][0]
        src_map[topo_ne_cell_cnt].append(src_map[topo_ne_cell_cnt].pop(0))
    return final_fdn_map


def write_metadata_for_ebsn_replay(writer_map):
    try:
        file_path = EBSN_METADATA_PATH + 'ebsn_scale_metadata.json_new'
        log_statement('INFO : Writing EBSN Replay Metadata information in dir {}.'.format(file_path))
        with open(file_path, 'w') as metadata_file:
            json.dump(writer_map, metadata_file, indent=2)
            metadata_file.flush()
        log_statement('INFO : EBSN Replay metadata information writing completed.')
    except Exception as e:
        log_statement('ERROR : Issue while writing metadata information for EBSN Replay.', 1)


def generate_file_information_for_ebsn_replay(final_map, max_proc):
    # { process_index_0 : { src_fdn : [ topology_fdn_1, topology_fdn_2,...] }, process_index_1 : ... }
    ebsn_metadata_map = defaultdict(lambda: defaultdict(list))
    log_statement('INFO : Generating metadata information for EBSN replay...')
    proc_counter = 0
    for topology_fdn, src_fdn in final_map.items():
        if proc_counter >= max_proc:
            proc_counter = 0
        ebsn_metadata_map[proc_counter][src_fdn].append(topology_fdn)
        proc_counter += 1
    log_statement('INFO : Metadata information has been generated successfully for EBSN Replay.')
    write_metadata_for_ebsn_replay(ebsn_metadata_map)


def check_fdn_compliance(_map):
    log_statement('INFO : Doing provided input source data verification for fdn and time...')
    fdn_list = sorted(_map[sorted(_map.keys())[0]].keys())
    for key, _c_map in _map.items():
        if fdn_list != sorted(_c_map.keys()):
            log_statement(
                'ERROR : Provided fdn(s) in input source not same with respect to name and count across all ROP(s).', 1)
    log_statement('INFO : Verification completed for fdn and time for input data source.')


def generate_rop_metadata_info(sorted_rop_keys):
    try:
        file_path = EBSN_METADATA_PATH + 'ebsn_rop_metadata.json_new'
        log_statement('INFO : Writing EBSN Replay ROP Metadata information in dir {}.'.format(file_path))
        with open(file_path, 'w') as metadata_file:
            json.dump(sorted_rop_keys, metadata_file, indent=2)
            metadata_file.flush()
        log_statement('INFO : EBSN Replay ROP metadata information writing completed.')
        log_statement('INFO : Process completed for EBSN Replay mapping.')
    except Exception as e:
        log_statement('ERROR : Issue while writing metadata information for EBSN Replay.', 1)


def generate_mapping_for_ebsn_replay():
    rop_map = collect_rop_information_for_ebsn()
    check_fdn_compliance(rop_map)
    ebsn_input_fdn_cell_map = parse_cell_info_from_ebsn_input_source(
        rop_map[sorted(rop_map.keys())[0]])  # ebsn_input_fdn_cell_map = { cell_cnt : input_fdn, ..}
    ebsn_topo_map = parse_nr_ebsn_topology_information()  # ebsn_top_map = { <ne_1> : <max_cell_count>, <ne_2> : <max_cell_count> }
    topo_fdn_to_src_fdn_map = mapping_ebsn_topology_to_source_fdn(ebsn_input_fdn_cell_map, ebsn_topo_map)
    ebsn_topo_map.clear(), ebsn_input_fdn_cell_map.clear()
    max_proc_cnt = 8
    if len(topo_fdn_to_src_fdn_map.keys()) < max_proc_cnt:
        max_proc_cnt = len(topo_fdn_to_src_fdn_map.keys())
    generate_file_information_for_ebsn_replay(topo_fdn_to_src_fdn_map, max_proc_cnt)
    generate_rop_metadata_info(sorted(rop_map.keys()))


def run_for_use_case():
    case_list = collect_use_case_info_from_netsim_cfg()
    if len(case_list) > 0:
        log_statement('INFO : Replay use case(s) collected.')
        for use_case in case_list:
            if use_case == 'EBSN_ESOA_PERFORMANCE':
                log_statement('INFO : Processing for EBSN Performance Replay use case.')
                generate_mapping_for_ebsn_replay()
    else:
        log_statement('WARNING : No replay use case found.', 0)


def main(args):
    global EBSN_SOURCE_PATH
    EBSN_SOURCE_PATH = args[0].strip()
    log_statement('INFO : Started process for static file mapping for PM Service.')
    run_for_use_case()
    log_statement('INFO : Static file mapping for PM Service is completed.')


if __name__ == '__main__':
    main(sys.argv[1:])

