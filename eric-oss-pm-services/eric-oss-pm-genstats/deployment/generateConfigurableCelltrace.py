#!/usr/bin/python -u
import errno
import json
import os
import sys
import traceback
from _collections import defaultdict
from multiprocessing import Pool

from utilityFunctions import Utility

util = Utility()

concurrent_process_count = 1

start_date_utc, start_time_utc, end_time_utc, epoch_rop_dir = '', '', '', ''
collect_result = 0


def fetch_network_information():
    if not util.checkFileExistance(util.netsim_cfg):
        util.printStatements('file {} not found.'.format(util.netsim_cfg), 'ERROR')
        return
    enm_id = util.get_value_from_netsim_cfg('ENM_ID=')
    if enm_id is not None:
        network_file = '/etc/config/.simulated_network_' + enm_id + '.json'
        if not util.checkFileExistance(network_file):
            util.printStatements('File {} not found.'.format(network_file), 'ERROR')
            return
        with open(network_file) as f:
            datastore = json.load(f)
            if 'GNODEBRADIO' in datastore:
                return datastore['GNODEBRADIO']
            else:
                return None


def create_sym_link_for_nr_celltrace(id, ne_list):
    parent_dir = '/ericsson/pmic/CELLTRACE/'
    source_files = util.ne_to_events_file[2]['GNODEBRADIO']['low']
    source_location = '/netsim_users/pms/rec_templates/'
    processed_count = 0
    if os.path.exists(parent_dir) and os.path.isdir(parent_dir):
        child_dir = 'SubNetwork=Europe,SubNetwork=Ireland,MeContext=<NODE>/' + epoch_rop_dir + '/'
        my_file_name = ''.join(util.events_file_format_mapping['GNODEBRADIO']['CELLTRACE'])
        my_file_name = my_file_name.replace('<START_DATE>', start_date_utc).replace('<START_TIME>',
                                                                                    start_time_utc).replace(
            '<END_TIME>', end_time_utc).replace('<FILE_ID>', '1_1_1')
        for ne in ne_list:
            ne_file_name = my_file_name.replace('<NODE>', ne)
            ne_file_path = parent_dir + child_dir.replace('<NODE>', ne)
            if not os.path.exists(ne_file_path):
                os.makedirs(ne_file_path, 0o755)
            for net_fun in ['CUCP', 'CUUP', 'DU']:
                final_file_name = ne_file_name.replace('<EventProducer>', net_fun)
                final_full_path = ne_file_path + final_file_name
                source_full_path = source_location + source_files[net_fun]
                try:
                    os.symlink(source_full_path, final_full_path)
                    processed_count += 1
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        traceback.print_exc()
                except Exception as x:
                    traceback.print_exc()
    else:
        util.printStatements('Path {} does not exists.'.format(parent_dir), 'ERROR')
    return processed_count


def callback_result(result):
    global collect_result
    if result:
        collect_result += result


def distribute_work(my_nr_ne_started_list):
    process_to_ne_map = defaultdict(list)
    index = 0
    for my_nr_ne in my_nr_ne_started_list:
        if index >= concurrent_process_count:
            index = 0
        process_to_ne_map[index].append(my_nr_ne)
        index += 1
    process_pool = Pool(concurrent_process_count)
    for proc_id, work_list in process_to_ne_map.items():
        process_pool.apply_async(create_sym_link_for_nr_celltrace, args=(proc_id, work_list), callback=callback_result)
    process_pool.close()
    process_pool.join()
    util.printStatements('Total {} NR celltrace files generated.'.format(collect_result), 'INFO')
    util.printStatements('Generation completed for number of NR ne is {}.'.format(collect_result // 3), 'INFO')


def filter_nodes_for_celltrace(nr_nes):
    if util.checkFileExistance(util.startedNodeInfoFile):
        started_nr_ne_list = []
        util.printStatements('Fetching started nodes information.', 'INFO')
        with open(util.startedNodeInfoFile) as f:
            for line in f:
                if 'gNodeBRadio' in line and '<CTR>' in line:
                    started_nr_ne_list.append(line.strip().split(' ')[0])
        started_nr_ne_list = list(set(nr_nes).intersection(set(started_nr_ne_list)))
        util.printStatements('Started node information has been fetched.', 'INFO')
        util.printStatements('Number of started nodes found is {}'.format(len(list(set(started_nr_ne_list)))), 'INFO')
        if len(started_nr_ne_list) > 0:
            started_nr_ne_list = sorted(list(set(started_nr_ne_list)))
            custom_ctr = util.get_value_from_netsim_cfg('custom_ctr=')
            if str(custom_ctr).upper() == 'TRUE':
                util.printStatements('Custom ctr use case is enabled.', 'INFO')
                custom_nr_cell_trace_file_count = 0
                with open('/etc/config/config.json') as config_file:
                    info = json.load(config_file)
                    if 'NR_CTR_FILES' in info:
                        custom_nr_cell_trace_file_count += (int(info['NR_CTR_FILES']) // 3)
                started_nr_ne_list = started_nr_ne_list[:custom_nr_cell_trace_file_count]
            util.printStatements('Generating NR Celltrace data for {} ne(s)'.format(len(started_nr_ne_list)), 'INFO')
            distribute_work(started_nr_ne_list)
        else:
            util.printStatements('No started node found for gNodeBRadio node category.', 'WARNING')
    else:
        util.printStatements('File {} not found'.format(util.startedNodeInfoFile), 'ERROR')


def fetchSimsNeList():
    nr_nes_in_network = []
    util.printStatements('Fetching network information...', 'INFO')
    network = fetch_network_information()
    util.printStatements('Network information has been fetched.', 'INFO')
    if network is not None:
        for sim_and_ne in network:
            nr_nes_in_network.append(sim_and_ne.split('|')[-1])
        util.printStatements('Found NR network with {} network element'.format(len(list(set(nr_nes_in_network)))),
                             'INFO')
        if len(nr_nes_in_network) > 0:
            filter_nodes_for_celltrace(nr_nes_in_network)
        else:
            util.printStatements('No sims found for node type gNodeBRadio in network file', 'ERROR')
    else:
        util.printStatements('No network found for gNodeBRadio', 'ERROR')


def main(argv):
    """
    argv : startDateTime, endDateTime, startOffset, endOffset
    """
    if argv:
        global start_date_utc, start_time_utc, end_time_utc, epoch_rop_dir
        start_date_utc, start_time_utc, end_time_utc, epoch_rop_dir = argv[0], argv[1], argv[2], argv[3]
        fetchSimsNeList()
    else:
        util.printStatements('Invalid arguments given.', 'ERROR', True)


if __name__ == '__main__':
    main(sys.argv[1:])
