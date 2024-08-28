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

nr_sims_per_enm, pcc_sims_per_enm, pcg_sims_per_enm = 0, 0, 0
nr_nes_per_sim, pcc_nes_per_sim, pcg_nes_per_sim = 0, 0, 0
nr_mim_release, pcc_mim_release, pcg_mim_release = None, None, None
total_started_nr_nes, total_started_pcc_nes, total_started_pcg_nes = 0, 0, 0

sim_dir_list = []
sim_data_list = []
started_ne_count_map = {}
exclude_ne_list = []

full_fdn = "SubNetwork=Europe,SubNetwork=Ireland,MeContext="

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
        for my_file in filter(None, os.listdir(config_map_path)):
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
    if 'GNODEBRADIO' in ne_type:
        os.system("python /netsim_users/pms/bin/nr_topology_parser.py " + os.path.join(config_map_path, constant.ENM_NETWORK_JSON.replace('<ENM_ID>', enm_id)))
    else:
        pass


def calculate_started_ne_for_this_enm(ne_type, total_started_ne):
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
    if ne == 'GNODEBRADIO':
        started_ne_count_map[ne] = calculate_started_ne_for_this_enm(ne, total_started_nr_nes)
    if ne == 'PCC':
        started_ne_count_map[ne] = calculate_started_ne_for_this_enm(ne, total_started_pcc_nes)
    if ne == 'PCG':
        started_ne_count_map[ne] = calculate_started_ne_for_this_enm(ne, total_started_pcg_nes)


def generate_schema():
    logger.print_info('Generating network schema...')
    global sim_dir_list, sim_data_list
    ne_network_info_map = defaultdict(list)
    for release, ne_list in constant.SUPPORTED_NE_MAP.iteritems():
        if release != release_ver:
            continue
        for ne in ne_list:
            if ne in exclude_ne_list:
                continue
            _tmp_sim_dir_list, _tmp_sim_data_list = [], []
            if ne == 'GNODEBRADIO':
                ne_config = function.get_ne_configuration(ne, release_ver)
                start_sim_id = calculate_schema_configuration(nr_sims_per_enm)
                _tmp_sim_dir_list, _tmp_sim_data_list = function.generate_schema_for_ne(ne_config, start_sim_id,
                                                                                        nr_sims_per_enm, nr_nes_per_sim,
                                                                                        nr_mim_release, 5)
            elif ne == 'PCC':
                ne_config = function.get_ne_configuration(ne, release_ver)
                start_sim_id = calculate_schema_configuration(pcc_sims_per_enm)
                _tmp_sim_dir_list, _tmp_sim_data_list = function.generate_schema_for_ne(ne_config, start_sim_id,
                                                                                        pcc_sims_per_enm,
                                                                                        pcc_nes_per_sim,
                                                                                        pcc_mim_release, 3)
            elif ne == 'PCG':
                ne_config = function.get_ne_configuration(ne, release_ver)
                start_sim_id = calculate_schema_configuration(pcg_sims_per_enm)
                _tmp_sim_dir_list, _tmp_sim_data_list = function.generate_schema_for_ne(ne_config, start_sim_id,
                                                                                        pcg_sims_per_enm,
                                                                                        pcg_nes_per_sim,
                                                                                        pcg_mim_release, 3)
            elif ne == 'LTE MSRBS-V2':
                pass
            elif ne == 'LTE ERBS':
                pass
            if len(_tmp_sim_dir_list) > 0:
                if ne not in ne_network_info_map.keys():
                    ne_network_info_map[ne] = []
                ne_network_info_map[ne].extend(_tmp_sim_dir_list)
                sim_dir_list.extend(_tmp_sim_dir_list)
            if len(_tmp_sim_data_list) > 0:
                sim_data_list.extend(_tmp_sim_data_list)
        write_network_information(ne_network_info_map)
        for ne in ne_list:
            generate_topology_information(ne)
    logger.print_info('Network schema generated.')


def generate_directories():
    logger.print_info('Generating directory structure...')
    for sim_dir in sim_dir_list:
        dir_name = full_fdn + sim_dir.split('|')[1]
        dir_name = constant.PMIC_LOC + dir_name
        try:
            if function.is_dir_exists(dir_name):
                os.chmod(dir_name, 0755)
            else:
                os.makedirs(dir_name, 0755)
        except Exception as e:
            logger.print_error('Issue while creating directory ' + dir_name)
            terminate_script(1)
    logger.print_info('Directory structures created.')


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
    logger.print_info('Reading network information for ENM : ' + enm_id)
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


def generate_started_ne_file():
    logger.print_info('Generating ' + constant.STARTED_NE_FILE + ' file.')
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
            for sim_dir in network_map[ne_type]:
                if ne_range == 0:
                    break
                sim_name, ne_name = sim_dir.split('|')
                line_info_list.append(
                    constant.START_NE_FORMAT.replace('<NODE_NAME>', ne_name).replace('<SIM_NAME>', sim_name))
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
        print e
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
        netsim_cfg_sim_list = list(set([x.split('|')[0] for x in sim_dir_list]))
        with open(constant.NETSIM_CFG, 'a') as f:
            f.write('\n')
            f.write('LIST="' + ' '.join(netsim_cfg_sim_list) + '"\n')
            f.flush()
    else:
        logger.print_error('File ' + constant.NETSIM_CFG + ' not found.')
        terminate_script(1)

def update_sim_info():
    _map = read_network_information()
    _tmp_dict = defaultdict(list)
    for key, values in _map.iteritems():
        _tmp_list = []
        for value in values:
            _tmp_list.append(value.split('|')[0])
        _tmp_list = list(set(_tmp_list))
        for sim in _tmp_list:
            _tmp_dict[key].append(sim)
    with open('/netsim/genstats/tmp/sim_info.txt', 'w') as f:
        for key, sims in _tmp_dict.iteritems():
            for sim in sims:
                f.write(sim + ':' + key + '\n')
        f.flush()

def initiate_deployment_configuration():
    logger.print_info('Deployment configuration request identified. Started worker.')
    do_cleanup_for_deploy_config(create_deploy_config_lock_file())
    generate_schema()
    generate_directories()
    generate_sim_data_list()
    update_sim_info()
    update_netsim_cfg()
    generate_started_ne_file()
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


'''
This below method block needs to be repalce with some generic logic
'''
def fetch_ne_params_from_config_map(json_map):
    global exclude_ne_list
    global nr_sims_per_enm, pcc_sims_per_enm, pcg_sims_per_enm
    global nr_nes_per_sim, pcc_nes_per_sim, pcg_nes_per_sim
    global total_started_nr_nes, total_started_pcc_nes, total_started_pcg_nes
    global nr_mim_release, pcc_mim_release, pcg_mim_release

    nr_sims_per_enm = function.get_int_value_from_json(json_map, constant.NR_SIMS_PER_ENM)
    pcc_sims_per_enm = function.get_int_value_from_json(json_map, constant.PCC_SIMS_PER_ENM)
    pcg_sims_per_enm = function.get_int_value_from_json(json_map, constant.PCG_SIMS_PER_ENM)

    nr_nes_per_sim = function.get_int_value_from_json(json_map, constant.NR_NES_PER_SIM)
    pcc_nes_per_sim = function.get_int_value_from_json(json_map, constant.PCC_NES_PER_SIM)
    pcg_nes_per_sim = function.get_int_value_from_json(json_map, constant.PCG_NES_PER_SIM)

    nr_mim_release = function.get_str_value_from_json(json_map, constant.NR_MIM_RELEASE)
    pcc_mim_release = function.get_str_value_from_json(json_map, constant.PCC_MIM_RELEASE)
    pcg_mim_release = function.get_str_value_from_json(json_map, constant.PCG_MIM_RELEASE)

    total_started_nr_nes = function.get_int_value_from_json(json_map, constant.TOTAL_STARTED_NR_NES)
    total_started_pcc_nes = function.get_int_value_from_json(json_map, constant.TOTAL_STARTED_PCC_NES)
    total_started_pcg_nes = function.get_int_value_from_json(json_map, constant.TOTAL_STARTED_PCG_NES)

    if None in [nr_sims_per_enm, nr_nes_per_sim, nr_mim_release] or 0 in [nr_sims_per_enm, nr_nes_per_sim]:
        exclude_ne_list.append('GNODEBRADIO')
        logger.print_info('Skipping network configuration for ne type : GNODEBRADIO')

    if None in [pcc_sims_per_enm, pcc_nes_per_sim, pcc_mim_release] or 0 in [pcc_sims_per_enm, pcc_nes_per_sim]:
        exclude_ne_list.append('PCC')
        logger.print_info('Skipping network configuration for ne type : PCC')

    if None in [pcg_sims_per_enm, pcg_nes_per_sim, pcg_mim_release] or 0 in [pcg_sims_per_enm, pcg_nes_per_sim]:
        exclude_ne_list.append('PCG')
        logger.print_info('Skipping network configuration for ne type : PCG')

    if total_started_nr_nes is None:
        total_started_nr_nes = 0
    if total_started_pcg_nes is None:
        total_started_pcg_nes = 0
    if total_started_pcc_nes is None:
        total_started_pcc_nes = 0


def fetch_config_map_param(json_map):
    global enm_index, total_enm
    # ENM_ID_LIST, NR_SIMS_PER_ENM, NR_NES_PER_SIM, TOTAL_NR_NES must needs to be present in config map
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
        logger.print_error('Invalid arguments given.')
        terminate_script(1)


if __name__ == '__main__':
    main(sys.argv[1:])
