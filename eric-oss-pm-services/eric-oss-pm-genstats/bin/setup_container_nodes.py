#!/usr/bin/python

# Created on Feb 09, 2023

# @author: xmanabh

import getopt
import json
import math
import os
import sys
from collections import defaultdict

from common_functions import CommonFunctions
from constants import Constants
from logger_utility import LoggerUtilities

logger = LoggerUtilities()
function = CommonFunctions()
constant = Constants()

log_location = constant.PMS_LOG_LOC + 'node_setup.log'

config_map_path = None
enm_id = None
release_ver = None

debug_mode = False

enm_index, total_enm = 0, 0

sim_dir_list = []
sim_data_list = []
started_ne_count_map = {}
exclude_ne_list = []


def terminate_script(status=0):
    logger.print_info('Terminating process.')
    sys.exit(status)


def help_message(status=0):
    print('Script calling arguments help : ')
    print('python setup_container_nodes.py -g deploy_config/scale_config')
    print('python setup_container_nodes.py --generate=deploy_config/scale_config')
    terminate_script(status)


def do_cleanup_for_deploy_config(ignore_file):
    logger.print_info('Cleaning up old deployment configuration...')
    try:
        my_file_list = [config_map_path + x + '_' + enm_id for x in constant.FULL_CLEANUP]
        for my_file in my_file_list:
            if my_file == ignore_file:
                continue
            if function.is_file_exists(my_file):
                function.remove_file_only(my_file)
            else:
                logger.log_debug('Skipping file removal ' + my_file + ' as file does not exists.')
        for my_file in [x for x in filter(None, os.listdir(config_map_path))]:
            if my_file.startswith('.simulated_network_') and my_file.endswith('.json'):
                function.remove_file_only(config_map_path + my_file)
        logger.print_info('Old deployment configuration cleanup completed.')
    except Exception as e:
        logger.print_error('Issue with cleaning up old configuration.')
        terminate_script(1)


def create_deploy_config_lock_file():
    filepath = config_map_path + constant.DEPLOYING + '_' + enm_id
    if not function.is_file_exists(filepath):
        with open(filepath, 'w') as f:
            pass
    return filepath


def remove_deploy_config_lock_file():
    filepath = config_map_path + constant.DEPLOYING + '_' + enm_id
    if function.is_file_exists(filepath):
        try:
            function.remove_file_only(filepath)
        except Exception as e:
            logger.print_error('Issue while removing file ' + filepath)
            terminate_script(1)


def calculate_schema_configuration(sims_per_enm):
    start_id = ((enm_index * sims_per_enm) + 1)
    return start_id


def generate_topology_information(ne_type):
    file_path = os.path.join(config_map_path, constant.ENM_NETWORK_JSON.replace('<ENM_ID>', enm_id))
    if ne_type == 'GNODEBRADIO':
        os.system('python /netsim_users/pms/bin/topology_parser.py "GNODEBRADIO" "' + file_path + '"')
    elif ne_type == 'GNODEBRADIO_EBSN':
        os.system('python /netsim_users/pms/bin/topology_parser.py "GNODEBRADIO_EBSN" "' + file_path + '"')
        source_file_path = '/netsim_users/pms/xml_templates/replay/CUCP/:/netsim_users/pms/xml_templates/replay/CUUP/:/netsim_users/pms/xml_templates/replay/DU/'
        run_command = 'python /netsim_users/pms/bin/pmStaticFileMapper.py "' + source_file_path + '"'
        os.system(run_command)
    elif ne_type == 'LTE':
        os.system('python /netsim_users/pms/bin/topology_parser.py "LTE" "' + file_path + '"')


def calculate_started_ne_for_this_enm(total_started_ne):
    temp_total_enm = total_enm
    for i in range(0, total_enm):
        mod = int(math.ceil(float(total_started_ne / (temp_total_enm * 1.0))))
        if enm_index == i:
            return mod
        total_started_ne = total_started_ne - mod
        temp_total_enm = temp_total_enm - 1
    return None


def write_network_information(_map):
    filepath = config_map_path + constant.ENM_NETWORK_JSON.replace('<ENM_ID>', enm_id)
    logger.print_info('Writing network information in file ' + filepath)
    try:
        with open(filepath, 'w') as f:
            json.dump(_map, f, indent=2)
        logger.print_info('Writing network information in file ' + filepath + ' completed.')
    except Exception as e:
        logger.print_error('Issue while writing network information in file ' + filepath)
        terminate_script(1)


def update_started_ne_map(ne):
    global started_ne_count_map
    for key, value in constant.identity_map.items():
        if ne == value.upper():
            started_ne_count_map[ne] = calculate_started_ne_for_this_enm(constant.total_started_ne_to_cnt_map[
                                                                             'TOTAL_STARTED_' + key + '_NES'])
            break


def generate_schema_for_ne(ne):
    if ne == 'LTE ERBS':
        return [], []
    ne_type = [x for x, y in constant.identity_map.items() if y == ne][0]
    ne_config = function.get_ne_configuration(ne, release_ver)
    ne_type_sims_per_enm, ne_type_nes_per_sim, ne_type_mim_release = ne_type + '_SIMS_PER_ENM', ne_type + '_NES_PER_SIM', ne_type + '_MIM_RELEASE'
    sims_per_enm, nes_per_sim, mim_release = constant.sims_per_enm_map[ne_type_sims_per_enm], \
        constant.nes_per_sim_map[ne_type_nes_per_sim], constant.ne_mim_release_map[ne_type_mim_release]
    start_sim_id = calculate_schema_configuration(sims_per_enm)
    return function.generate_schema_for_ne(ne_config, start_sim_id,
                                           sims_per_enm, nes_per_sim,
                                           mim_release, 5)


def generate_schema():
    logger.print_info('Generating network schema...')
    global sim_dir_list, sim_data_list
    ne_network_info_map = defaultdict(list)
    for release, ne_list in constant.SUPPORTED_NE_MAP.items():
        if release != release_ver:
            continue
        for ne_map in ne_list:
            for ne in ne_map.keys():
                if ne in exclude_ne_list:
                    continue
                _tmp_sim_dir_list, _tmp_sim_data_list = generate_schema_for_ne(ne)
                if len(_tmp_sim_dir_list) > 0:
                    if ne not in ne_network_info_map.keys():
                        ne_network_info_map[ne] = []
                    ne_network_info_map[ne].extend(_tmp_sim_dir_list)
                    sim_dir_list.extend(_tmp_sim_dir_list)
                if len(_tmp_sim_data_list) > 0:
                    sim_data_list.extend(_tmp_sim_data_list)
        write_network_information(ne_network_info_map)
        for ne in ne_list:
            generate_topology_information(list(ne.keys())[0])
    logger.print_info('Network schema generated.')


def create_dirs(dir_list):
    try:
        for dir_name in dir_list:
            if function.is_dir_exists(dir_name):
                os.chmod(dir_name, 0o755)
            else:
                os.makedirs(dir_name, 0o755)
    except Exception as e:
        logger.print_error('Issue while creating directory ' + dir_name)
        terminate_script(1)


def generate_directories(ne_type, data_type_list, dirs):
    if ne_type == 'GNODEBRADIO_EBSN':
        create_dirs([constant.PMIC_LOC + 'REPLAY/NR_EBSN_' + x for x in ['CUCP', 'CUUP', 'DU']])
        return
    else:
        counter = 0
        dir_path_list = []
        for dir in dirs:
            ne_name = dir.split('|')[1]
            for data_type in data_type_list:
                if data_type == 'FUTURE':
                    if counter < constant.FUTURE_NODE_LIMIT:
                        counter += 1
                    else:
                        continue
                dir_path = constant.PMIC_LOC + data_type + '/' + constant.FULL_FDN_FORMAT
                if ne_type in ['PCC', 'PCC_AMF', 'PCG']:
                    dir_path = dir_path.replace('<subnet>', constant.SUB_NET_MAP[ne_type]) + ne_name + \
                               constant.MANAGED_ELEMENT_MAP[ne_type] + ne_name
                else:
                    dir_path = dir_path.replace('<subnet>', constant.SUB_NET_MAP['DEFAULT']) + ne_name
                dir_path_list.append(dir_path)
        if len(dir_path_list) > 0:
            create_dirs(dir_path_list)


def generate_data_directories():
    logger.print_info('Generating directory structure...')
    for ne_map in constant.SUPPORTED_NE_MAP[release_ver]:
        for ne_type, data_type_list in ne_map.items():
            if ne_type in exclude_ne_list:
                continue
            dirs_for_ne_type = read_network_information()[ne_type]
            generate_directories(ne_type, data_type_list, dirs_for_ne_type)


def generate_sim_data_list():
    logger.print_info('Generating ' + constant.SIM_DATA_FILE + ' file.')
    try:
        with open(constant.SIM_DATA_FILE, 'w') as f:
            for line in sim_data_list:
                f.write(line)
            f.flush()
        logger.print_info(constant.SIM_DATA_FILE + ' file generated.')
    except Exception as e:
        logger.print_error('Issue while generating ' + constant.SIM_DATA_FILE + ' file.')
        terminate_script(1)


def read_network_information():
    filepath = config_map_path + constant.ENM_NETWORK_JSON.replace('<ENM_ID>', enm_id)
    _map = None
    if function.is_file_exists(filepath):
        try:
            with open(filepath, 'r') as f:
                _map = json.load(f)
        except Exception as e:
            logger.print_error('Issue while reading network information from file ' + filepath)
            terminate_script()
    else:
        logger.print_error('File ' + filepath + ' not exist.')
        terminate_script(1)
    return _map


def get_maximum_started_range(file_range, regex, current_format):
    if file_range is None or file_range <= 0:
        started_ne_format = current_format.replace(regex, '')
    else:
        started_ne_format = current_format
        file_range -= 1
    return file_range, started_ne_format


def generate_started_ne_file():
    logger.print_info('Generating ' + constant.STARTED_NE_FILE + ' file.')
    stats_range = 0
    ctr_range = 0
    try:
        network_map = read_network_information()
        if network_map is None:
            logger.print_warn('No network information available.')
            terminate_script(1)
        for ne in network_map.keys():
            update_started_ne_map(ne)
        line_info_list = []
        for ne_type in started_ne_count_map.keys():
            ne_range = started_ne_count_map[ne_type]

            if ne_range is None:
                logger.print_error('None return for ne ' + ne_type + ' for started node count. Please check.')
                terminate_script(1)

            # Fetch max stats / events files to be generated for this ne_type from config file, if not exists then values will be 0.
            for key, value in constant.identity_map.items():
                if ne_type == value:
                    stats_range = constant.ne_stats_files.get(key + "_STATS_FILES", 0)
                    ctr_range = constant.ne_ctr_files.get(key + "_CTR_FILES", 0)
                    if key == "NR":
                        ctr_range = ctr_range // 3
                    break

            # Build the started ne file
            for sim_dir in network_map[ne_type]:
                started_ne_format = constant.START_NE_FORMAT
                if ne_range == 0:
                    break
                sim_name, ne_name = sim_dir.split('|')
                for file_type, max_range in constant.custom_file_map.items():
                    if "stats" in file_type and constant.custom_file_map["custom_stats"] == "true":
                        stats_range, started_ne_format = get_maximum_started_range(stats_range, '<STATS>',
                                                                                   started_ne_format)
                    elif "ctr" in file_type and constant.custom_file_map["custom_ctr"] == "true":
                        ctr_range, started_ne_format = get_maximum_started_range(ctr_range, '<CTR>', started_ne_format)
                    else:
                        started_ne_format = constant.START_NE_FORMAT
                line_info_list.append(
                    started_ne_format.replace('<NODE_NAME>', ne_name).replace('<SIM_NAME>', sim_name))
                ne_range = ne_range - 1
        try:
            with open(constant.STARTED_NE_FILE, 'w') as f:
                if len(line_info_list) > 0:
                    for line in line_info_list:
                        f.write(line)
                else:
                    logger.print_info('Seems like no nodes are started.')
                f.flush()
            logger.print_info('File ' + constant.STARTED_NE_FILE + ' generated successfully.')
        except Exception as e:
            logger.print_error('Issue while generating ' + constant.STARTED_NE_FILE + ' file.')
            terminate_script(1)
    except Exception as e:
        print (e)
        logger.print_error('Issue while collecting started node information.')
        terminate_script(1)


def create_scale_ready_file():
    filepath = config_map_path + constant.SCALE_READY + '_' + enm_id
    if not function.is_file_exists(filepath):
        with open(filepath, 'w') as f:
            pass
    else:
        logger.print_error('File ' + constant.SCALE_READY + ' should not exist while deploying configuration.')
        terminate_script(1)


def update_netsim_cfg():
    if function.is_file_exists(constant.NETSIM_CFG):
        playback_cfg_sim_list = list(set([sim.split('|')[0] for sim in sim_dir_list if 'vDU' in sim or 'vCU' in sim]))

        # Sort this due to processing LTE_DG2 first.
        # Current priority is LTE_DG2 > NR > PCC/PCG >>
        netsim_cfg_sim_list = list(set([x.split('|')[0].split('-')[-1] for x in sim_dir_list if 'dg2' in x]))
        netsim_cfg_sim_list += sorted(
            list(set([x.split('|')[0] for x in sim_dir_list if
                      'dg2' not in x and 'vDU' not in x and 'vCU' not in x and 'EBSgNodeBRadio' not in x])),
            reverse=True)

        with open(constant.NETSIM_CFG, 'a') as f:
            f.write('\n')
            f.write('PLAYBACK_SIM_LIST="' + ' '.join(playback_cfg_sim_list) + '"\n\n')
            f.write('LIST="' + ' '.join(netsim_cfg_sim_list) + '"\n')
            f.flush()
    else:
        logger.print_error('File ' + constant.NETSIM_CFG + ' not found.')
        terminate_script(1)


def update_sim_info():
    _map = read_network_information()
    _tmp_dict = defaultdict(list)
    for key, values in _map.items():
        _tmp_list = []
        for value in values:
            _tmp_list.append(value.split('|')[0])
        _tmp_list = list(set(_tmp_list))
        for sim in _tmp_list:
            _tmp_dict[key].append(sim)
    with open('/netsim/genstats/tmp/sim_info.txt', 'w') as f:
        for key, sims in _tmp_dict.items():
            modified_key = key
            if key == 'PCC_AMF':
                modified_key = 'PCC'
            for sim in sims:
                f.write(sim + ':' + modified_key + '\n')
        f.flush()


def update_celltrace_relations():
    _map = read_network_information()
    json_map = {}
    for key, values in _map.items():
        _tmp_list = []
        for value in values:
            _tmp_list.append(value.split('|')[0])
        _tmp_list = list(set(_tmp_list))
        for sim in _tmp_list:
            if "NR" in sim:
                new_celltrace_entry = constant.NR_TEMPLATE.replace("<SIM>", sim)
                json_map[new_celltrace_entry] = ["/pm_data_DU/", "/pm_data_CUUP/", "/pm_data_CUCP/"]
    with open("/netsim_users/pms/etc/.celltrace_info.json", "w") as f:
        json.dump(json_map, f)


def initiate_deployment_configuration():
    logger.print_info('Deployment configuration request identified. Started worker.')
    do_cleanup_for_deploy_config(create_deploy_config_lock_file())
    generate_schema()
    generate_sim_data_list()
    update_sim_info()
    update_netsim_cfg()
    update_celltrace_relations()
    generate_started_ne_file()
    generate_data_directories()
    remove_deploy_config_lock_file()
    create_scale_ready_file()
    logger.print_info('Deployment configuration completed.')


def remove_scaling_lock_file():
    filepath = config_map_path + constant.SCALING + '_' + enm_id
    if function.is_file_exists(filepath):
        try:
            function.remove_file_only(filepath)
        except Exception as e:
            logger.print_error('Issue while deleting file ' + filepath)
            terminate_script(1)
    else:
        logger.print_error('File ' + filepath + ' not exist. Something is wrong, please check')
        terminate_script(1)


def create_scaling_lock_file():
    filepath = config_map_path + constant.SCALING + '_' + enm_id
    if function.is_file_exists(filepath):
        logger.print_warn('Another instance of scaling script already running. Skipping this execution.')
        return False
    else:
        try:
            with open(filepath, 'w') as f:
                return True
        except Exception as e:
            logger.print_error('Issue while creating file ' + filepath)
            return False


def check_scaling_acceptance():
    filepath = config_map_path + constant.SCALE_READY + '_' + enm_id
    if not function.is_file_exists(filepath):
        logger.print_error('Not able to find ' + filepath + ' file. Check network deployed properly.')
        return False
    return create_scaling_lock_file()


def initiate_scaling_configuration():
    logger.print_info('Scaling configuration request identified. Started worker.')
    if not check_scaling_acceptance():
        terminate_script(1)
    generate_started_ne_file()
    remove_scaling_lock_file()
    logger.print_info('Scaling completed.')


def fetch_ne_params_from_config_map(json_map):
    global exclude_ne_list
    global nr_ctr_files, dg2_ctr_files

    sims_per_enm_keys, nes_per_sim_keys = constant.sims_per_enm_map.keys(), constant.nes_per_sim_map.keys()
    total_started_ne_to_cnt_keys, ne_mim_release_keys = constant.total_started_ne_to_cnt_map.keys(), constant.ne_mim_release_map.keys()
    ne_stats_files, ne_ctr_files = constant.ne_stats_files.keys(), constant.ne_ctr_files.keys()
    custom_file_keys = constant.custom_file_map.keys()

    for sims_per_enm_key in sims_per_enm_keys:
        constant.sims_per_enm_map[sims_per_enm_key] = function.get_int_value_from_json(json_map, sims_per_enm_key)
        if constant.sims_per_enm_map[sims_per_enm_key] in [None, 0]:
            exclude_ne_list.append(function.get_node_identity_from_param(sims_per_enm_key))

    for nes_per_sim_key in nes_per_sim_keys:
        constant.nes_per_sim_map[nes_per_sim_key] = function.get_int_value_from_json(json_map, nes_per_sim_key)
        if constant.nes_per_sim_map[nes_per_sim_key] in [None, 0]:
            exclude_ne_list.append(function.get_node_identity_from_param(nes_per_sim_key))

    for total_started_ne_to_cnt_key in total_started_ne_to_cnt_keys:
        constant.total_started_ne_to_cnt_map[total_started_ne_to_cnt_key] = function.get_int_value_from_json(json_map,
                                                                                                             total_started_ne_to_cnt_key)
        if constant.total_started_ne_to_cnt_map[total_started_ne_to_cnt_key] is None:
            constant.total_started_ne_to_cnt_map[total_started_ne_to_cnt_key] = 0

    for ne_mim_release_key in ne_mim_release_keys:
        constant.ne_mim_release_map[ne_mim_release_key] = function.get_str_list_object_from_json(json_map,
                                                                                                 ne_mim_release_key)
        if constant.ne_mim_release_map[ne_mim_release_key] is None:
            exclude_ne_list.append(function.get_node_identity_from_param(ne_mim_release_key))

    for ne_stats_file in ne_stats_files:
        constant.ne_stats_files[ne_stats_file] = function.get_int_value_from_json(json_map, ne_stats_file)

    for ne_ctr_file in ne_ctr_files:
        constant.ne_ctr_files[ne_ctr_file] = function.get_int_value_from_json(json_map, ne_ctr_file)

    for custom_file in custom_file_keys:
        constant.custom_file_map[custom_file] = os.getenv(custom_file)

    exclude_ne_list = list(set(exclude_ne_list))
    if len(exclude_ne_list) > 0:
        logger.print_info('Skipping network configuration for ne type(s) : [{}]'.format(', '.join(exclude_ne_list)))


def fetch_config_map_param(json_map):
    global enm_index, total_enm
    enm_id_list = function.get_str_list_object_from_json(json_map, constant.ENM_ID_LIST, True)
    if enm_id_list is None or len(enm_id_list) == 0:
        logger.print_error(
            'Either parameter ENM_ID_LIST is not present or ENM_ID_LIST not having any value in config map.')
        terminate_script(1)
    enm_id_list = sorted(enm_id_list, key=lambda item: int(item.split('_')[1]))
    total_enm = len(enm_id_list)
    enm_index = enm_id_list.index(enm_id)
    fetch_ne_params_from_config_map(json_map)


def load_main_config_map():
    filepath = config_map_path + constant.CONFIG_JSON
    if not function.is_file_exists(filepath):
        logger.print_error('Not able to locate config map : ' + filepath + '.')
        terminate_script(1)
    logger.print_info('Loading config map values from ' + filepath)
    config_json = function.get_json_object(filepath)
    if config_json is None:
        logger.print_error('Issue while reading config map json ' + filepath + '.')
        terminate_script(1)
    fetch_config_map_param(config_json)
    logger.print_info('Loading completed.')


def load_netsim_cfg():
    logger.print_info('Loading ' + constant.NETSIM_CFG + '...')
    # ENM_ID, CONFIG_MAP_LOC, RELEASE parameter must needs to be present in netsim_cfg
    global enm_id, config_map_path, release_ver
    enm_id = function.find_param_value_from_netsim_cfg(constant.ENM_ID)
    config_map_path = function.find_param_value_from_netsim_cfg(constant.CONFIG_MAP_PATH)
    release_ver = function.find_param_value_from_netsim_cfg(constant.RELEASE)
    if None in [enm_id, config_map_path, release_ver]:
        logger.print_error(
            'Not able to find either ENM_ID or CONFIG_MAP_PATH or RELEASE in the ' + constant.NETSIM_CFG + ' file.')
        terminate_script(1)
    else:
        config_map_path = function.correct_dir_path(config_map_path)
        logger.log_debug('ENM_ID found with value : ' + enm_id + ' in ' + constant.NETSIM_CFG + ' file.')
        logger.log_debug(
            'CONFIG_MAP_PATH found with value : ' + config_map_path + ' in ' + constant.NETSIM_CFG + ' file.')
        logger.log_debug('RELEASE Version found with value : ' + release_ver + ' in ' + constant.NETSIM_CFG + ' file.')
    logger.print_info('Loading completed.')


def identify_process(module):
    if not function.is_file_exists(constant.NETSIM_CFG):
        logger.print_error('Not able to find ' + constant.NETSIM_CFG + '.')
        terminate_script(1)
    load_netsim_cfg()
    load_main_config_map()
    if module == 'deploy_config':
        initiate_deployment_configuration()
    elif module == 'scale_config':
        initiate_scaling_configuration()
    logger.print_info('Process completed.')


def main(args):
    logger.set_is_debug_value(debug_mode)
    logger.print_info('Starting process...')
    try:
        logger.print_info('Capturing script arguments...')
        opts, args = getopt.getopt(args, 'g:h:', ['generate=', 'help='])
        logger.print_info('Script arguments captured.')
        logger.print_info('Processing arguments...')
        for opt, arg in opts:
            if opt in ('-g', '--generate'):
                if arg.lower() in ('deploy_config', 'scale_config'):
                    identify_process(arg.lower())
                else:
                    help_message(1)
            else:
                help_message(1)
        logger.print_info('Script arguments processed.')
    except Exception as e:
        print (e)
        logger.print_error('Invalid arguments given.')
        terminate_script(1)


if __name__ == '__main__':
    main(sys.argv[1:])


