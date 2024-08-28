#!/usr/bin/python -u

# Created on January, 24 by @xmanabh

import getopt
import gzip
import json
import os.path
import sys
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool
from traceback import print_exc

LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
EBSN_PM_PATH = '/ericsson/pmic/REPLAY/<NET_FUN>/<EPOCH>/'
EBSN_SRC_TEMPLATE_PATH = '/netsim_users/pms/xml_templates/replay/'
EBSN_SRC_NE_TO_TOPO_NE_FILE = '/netsim_users/pms/etc/ebsn_scale_metadata.json'
EBSN_SRC_ROP_INFO_FILE = '/netsim_users/pms/etc/ebsn_rop_metadata.json'
EBSN_COUNTER_INFO_JSON = ''

gen_file_count = 0

EBSN_NET_FUN_DIR_MAP = {'CUUP': 'NR_EBSN_CUUP', 'CUCP': 'NR_EBSN_CUCP', 'DU': 'NR_EBSN_DU'}

START_TIME, END_TIME, DURATION, EBSN_DEST_FILE_FORMAT = None, None, None, None

SRC_NE_TO_TEMPLATE_MAP = defaultdict(list)
SRC_TEMPLATE_TO_FIELD_MAP = defaultdict(lambda: defaultdict(list))
SRC_TEMP_MEASOBJ_COUNTER_POS_MAP = defaultdict(lambda: defaultdict(lambda: defaultdict()))
SRC_TEMPLATE_TO_DATA_MAP = defaultdict(list)
EBSN_PM_DIR_MAP = {}

EBSN_COUNTER_VALUE_INFO = None


def result_count(count):
    global gen_file_count
    gen_file_count = gen_file_count + count


def terminate_script(status=0):
    sys.exit(status)


def help_message(status=0):
    print('ERROR : Invalid arguments given.')
    print(
        'INFO : Calling arguments >> python <script_name>.py -s <start_time> -e <end_time> -d <duration> -t <time_epoch>')
    terminate_script(status)


def move_json_files():
    try:
        for f in [EBSN_SRC_NE_TO_TOPO_NE_FILE, EBSN_SRC_ROP_INFO_FILE]:
            new_file = f + '_new'
            if os.path.exists(new_file):
                log_statement('INFO : Moving file {} to {}'.format(new_file, f))
                if os.path.exists(f):
                    os.remove(f)
                os.rename(new_file, f)
                log_statement('INFO : File moved successfully.')
    except:
        log_statement('ERROR : Issue with moving/renaming metadata json file.', 1)


def update_source_template_rop_time_in_json(input_list):
    try:
        with open(EBSN_SRC_ROP_INFO_FILE, 'w') as f:
            json.dump(input_list, f, indent=2)
            f.flush()
    except:
        log_statement('ERROR : Issue while writing information in file {}'.format(EBSN_SRC_ROP_INFO_FILE), 1)


def fetch_source_templates(rop_time):
    global SRC_NE_TO_TEMPLATE_MAP
    for net_fun in EBSN_NET_FUN_DIR_MAP.keys():
        dir_path = EBSN_SRC_TEMPLATE_PATH + net_fun
        for template in [x for x in filter(None, os.listdir(dir_path))]:
            if template.startswith(rop_time) and template.endswith('.xml'):
                fdn, template_full_path = template.split('_')[1], dir_path + '/' + template
                SRC_NE_TO_TEMPLATE_MAP[fdn].append(template_full_path)
                update_and_fetch_template_data(template_full_path)


def get_source_template_for_rop_time():
    try:
        with open(EBSN_SRC_ROP_INFO_FILE) as f:
            rop_list = [x for x in filter(None, json.load(f))]
            if rop_list is None or len(rop_list) == 0:
                log_statement('ERROR : No rop time information found in file {}'.format(EBSN_SRC_ROP_INFO_FILE), 1)
            rop_time = rop_list.pop(0)
            rop_list.append(rop_time)
            update_source_template_rop_time_in_json(rop_list)
            fetch_source_templates('A' + rop_time)
    except:
        log_statement('ERROR : Issue while operating file {}'.format(EBSN_SRC_ROP_INFO_FILE), 1)


def consume_parallel_processing_metadata_json():
    try:
        process_metadata = None
        with open(EBSN_SRC_NE_TO_TOPO_NE_FILE) as f:
            process_metadata = json.load(f)
        if process_metadata is not None and len(process_metadata.keys()) > 0:
            return process_metadata
        else:
            log_statement('ERROR : No information found in file {}'.format(EBSN_SRC_NE_TO_TOPO_NE_FILE), 1)
    except:
        log_statement(
            'ERROR : Issue while reading parallel processing metadata from file {}'.format(EBSN_SRC_NE_TO_TOPO_NE_FILE),
            1)


def generate_pm_dirs():
    try:
        global EBSN_PM_DIR_MAP
        for net_fun, dir_name in EBSN_NET_FUN_DIR_MAP.items():
            dir_path = EBSN_PM_PATH.replace('<NET_FUN>', dir_name)
            EBSN_PM_DIR_MAP[net_fun] = dir_path
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, 0o755)
    except:
        log_statement('ERROR : Issue while generating pm path directory for EBSN.', 1)


def log_statement(msg, exit_value=None):
    print(get_current_date_time() + msg)
    if exit_value is not None:
        terminate_script(exit_value)


def get_current_date_time():
    return datetime.now().strftime(LOG_TIME_FORMAT) + ' '


def generate_pm_stats_file_copy(src_to_topo_nes):
    files_generated = 0
    try:
        for src_fdn, topo_fdn_list in src_to_topo_nes.items():
            src_short_fdn = src_fdn.split('=')[-1]
            for topo_fdn in topo_fdn_list:
                topo_full_fdn = 'SubNetwork=Europe,SubNetwork=Ireland,MeContext=<SHORT_FDN>,ManagedElement=<SHORT_FDN>'.replace(
                    '<SHORT_FDN>', topo_fdn)
                target_file_format = EBSN_DEST_FILE_FORMAT.replace('<TOPO_FULL_FDN>', topo_full_fdn)
                for src_template in SRC_NE_TO_TEMPLATE_MAP[src_fdn]:
                    for net_fun in ['CUCP', 'CUUP', 'DU']:
                        if net_fun in src_template:
                            target_file_name = EBSN_PM_DIR_MAP[net_fun] + target_file_format.replace('<NET_FUN>',
                                                                                                     net_fun)
                            template_pm_stats_info = SRC_TEMPLATE_TO_DATA_MAP[src_template]
                            template_field_info = SRC_TEMPLATE_TO_FIELD_MAP[src_template]

                            template_measobj_counter_info = {}
                            for src_measObjLdn in SRC_TEMP_MEASOBJ_COUNTER_POS_MAP[src_template]:
                                template_measobj_counter_info[
                                    src_measObjLdn.replace(src_short_fdn, topo_fdn)] = \
                                    SRC_TEMP_MEASOBJ_COUNTER_POS_MAP[src_template][src_measObjLdn]

                            target_file_data_list = []

                            # Handling fileSender
                            start_index, end_index = 0, 0
                            end_index = int(template_field_info['fileSender'][0])
                            target_file_data_list.extend(template_pm_stats_info[start_index:end_index])
                            target_file_data_list.append(
                                template_pm_stats_info[end_index].replace(src_fdn, topo_full_fdn))

                            # Handling managedElement
                            start_index = end_index + 1
                            end_index = int(template_field_info['managedElement'][0])
                            target_file_data_list.extend(template_pm_stats_info[start_index:end_index])
                            target_file_data_list.append(
                                template_pm_stats_info[end_index].replace(src_fdn, topo_full_fdn).replace(
                                    src_short_fdn, topo_fdn))

                            # Handling measValue
                            start_index = end_index + 1
                            for measIndex in template_field_info['measValue']:
                                target_file_data_list.extend(template_pm_stats_info[start_index:measIndex])
                                target_file_data_list.append(
                                    template_pm_stats_info[measIndex].replace(src_short_fdn, topo_fdn))
                                start_index = measIndex + 1

                            # Handling rest of the pm information
                            target_file_data_list.extend(template_pm_stats_info[start_index:])

                            '''
                            if target_fdn in csv_json:
                                for meas_line in template_measobj_counter_info:
                                    if meas_line in csv_json[target_fdn]:
                                        if beginTime matched?
                                            for counter, value in csv_json[target_fdn][meas_line][beginTime].items():
                                                counter_pos = template_measobj_counter_info[meas_line][counter]
                                                element = target_file_data_list[counter_pos]
                                                target_file_data_list[counter_pos] = element.split('>')[0] + '>' + value + '<' + element.split('<')[-1]

                            '''

                            current_file_object = None
                            try:
                                current_file_object = gzip.open(target_file_name, 'wt')
                                current_file_object.write(''.join(target_file_data_list))
                                files_generated += 1
                            except KeyboardInterrupt as k:
                                log_statement('ERROR : Key board interrupt received.')
                                print_exc()
                                return files_generated
                            except Exception as e:
                                log_statement(
                                    'ERROR : Issue with writing file {} using source {}'.format(target_file_name,
                                                                                                src_template))
                                print_exc()
                            finally:
                                if current_file_object is not None:
                                    current_file_object.flush()
                                    current_file_object.close()
                            break
    except KeyboardInterrupt as a:
        log_statement('ERROR : Key board interrupt received.')
        print_exc()
        return files_generated
    except Exception as x:
        log_statement('ERROR : Issue while generating pm stats file for EBSN in worker.')
        print_exc()
        return files_generated
    finally:
        return files_generated


def generate_pm_stats_file(src_to_topo_nes, ebsn_target_file_format, src_ne_to_templates, src_temp_field_info_map_str,
                           src_temp_measobj_counter_pos_map_str,
                           src_temp_pm_stats_info_map):
    files_generated = 0
    try:
        src_temp_field_info_map, src_temp_measobj_counter_pos_map = json.loads(src_temp_field_info_map_str), json.loads(
            src_temp_measobj_counter_pos_map_str)
        for src_fdn, topo_fdn_list in src_to_topo_nes.items():
            src_short_fdn = src_fdn.split('=')[-1]
            for topo_fdn in topo_fdn_list:
                topo_full_fdn = 'SubNetwork=Europe,SubNetwork=Ireland,MeContext=<SHORT_FDN>,ManagedElement=<SHORT_FDN>'.replace(
                    '<SHORT_FDN>', topo_fdn)
                target_file_format = ebsn_target_file_format.replace('<TOPO_FULL_FDN>', topo_full_fdn)
                for src_template in src_ne_to_templates[src_fdn]:
                    for net_fun in ['CUCP', 'CUUP', 'DU']:
                        if net_fun in src_template:
                            target_file_name = EBSN_PM_DIR_MAP[net_fun] + target_file_format.replace('<NET_FUN>',
                                                                                                     net_fun)
                            template_pm_stats_info = src_temp_pm_stats_info_map[src_template]
                            template_field_info = src_temp_field_info_map[src_template]

                            template_measobj_counter_info = {}
                            for src_measObjLdn in src_temp_measobj_counter_pos_map[src_template]:
                                template_measobj_counter_info[
                                    src_measObjLdn.replace(src_short_fdn, topo_fdn)] = src_measObjLdn

                            target_file_data_list = []

                            # Handling fileSender
                            start_index, end_index = 0, 0
                            end_index = int(template_field_info['fileSender'][0])
                            target_file_data_list.extend(template_pm_stats_info[start_index:end_index])
                            target_file_data_list.append(
                                template_pm_stats_info[end_index].replace(src_fdn, topo_full_fdn))

                            # Handling managedElement
                            start_index = end_index + 1
                            end_index = int(template_field_info['managedElement'][0])
                            target_file_data_list.extend(template_pm_stats_info[start_index:end_index])
                            target_file_data_list.append(
                                template_pm_stats_info[end_index].replace(src_fdn, topo_full_fdn).replace(
                                    src_short_fdn, topo_fdn))

                            # Handling measValue
                            start_index = end_index + 1
                            for measIndex in template_field_info['measValue']:
                                target_file_data_list.extend(template_pm_stats_info[start_index:int(measIndex)])
                                target_file_data_list.append(
                                    template_pm_stats_info[int(measIndex)].replace(src_short_fdn, topo_fdn))
                                start_index = int(measIndex) + 1

                            # Handling rest of the pm information
                            target_file_data_list.extend(template_pm_stats_info[start_index:])

                            '''
                                1. check begin time from csv json if valid then proceed or skip
                                2. check target fdn from csv json if matches with topo fdn and net fun the proceed or skip
                                3. iterate on csv json measobjLdn and compare csv json measObjLdn present in template_measobj_counter_info in key
                                    if present then iterate on csv json measObjLdn counter and value and get those counter position from \
                                    src_temp_measobj_counter_pos_map[src_template][template_measobj_counter_info[csv json measObjLdn]][counter_name] <- \
                                    This will give you position. Now change value in target_file_data_list using position and value in same list
                            '''

                            current_file_object = None
                            try:
                                current_file_object = gzip.open(target_file_name, 'wt')
                                current_file_object.write(''.join(target_file_data_list))
                                files_generated += 1
                            except KeyboardInterrupt as k:
                                log_statement('ERROR : Key board interrupt received.')
                                print_exc()
                                return files_generated
                            except Exception as e:
                                log_statement(
                                    'ERROR : Issue with writing file {} using source {}'.format(target_file_name,
                                                                                                src_template))
                                print_exc()
                            finally:
                                if current_file_object is not None:
                                    current_file_object.flush()
                                    current_file_object.close()
                            break
    except KeyboardInterrupt as a:
        log_statement('ERROR : Key board interrupt received.')
        print_exc()
        return files_generated
    except Exception as x:
        log_statement('ERROR : Issue while generating pm stats file for EBSN in worker.')
        print_exc()
        return files_generated
    finally:
        return files_generated


def initiate_worker(proc_map):
    '''
    SRC_TMP_TO_FIELD_MAP_STR, SRC_TEMP_MEASOBJ_COUNTER_POS_MAP_STR = json.dumps(SRC_TEMPLATE_TO_FIELD_MAP), json.dumps(
        SRC_TEMP_MEASOBJ_COUNTER_POS_MAP)
    '''
    proc_pool = None
    try:
        proc_pool = Pool(len(proc_map.keys()))
        for proc_id in proc_map.keys():
            proc_pool.apply_async(generate_pm_stats_file_copy, args=(proc_map[proc_id],), callback=result_count)
            '''
            proc_pool.apply_async(generate_pm_stats_file, args=(
                proc_map[proc_id], EBSN_DEST_FILE_FORMAT, SRC_NE_TO_TEMPLATE_MAP, SRC_TMP_TO_FIELD_MAP_STR,
                SRC_TEMP_MEASOBJ_COUNTER_POS_MAP_STR,
                SRC_TEMPLATE_TO_DATA_MAP), callback=result_count)
            '''
        proc_pool.close()
        proc_pool.join()
    except KeyboardInterrupt as k:
        log_statement('ERROR : Acknowledged Key Board Interrupt. Terminating all worker processes.')
        proc_pool.close()
        proc_pool.terminate()
    except Exception as e:
        log_statement('ERROR : Issue while generating pm stats information for EBSN. Terminating all worker processes.')
        proc_pool.close()
        proc_pool.terminate()
    finally:
        if proc_pool is not None:
            proc_pool.close()
            proc_pool.terminate()
        log_statement('INFO : Total file count generated for EBSN is : {}'.format(gen_file_count))


def update_and_fetch_template_data(template_file):
    global SRC_TEMPLATE_TO_DATA_MAP, SRC_TEMPLATE_TO_FIELD_MAP, SRC_TEMP_MEASOBJ_COUNTER_POS_MAP
    try:
        short_fdn = os.path.basename(template_file).split('ManagedElement=')[-1].split('_')[0]
        with open(template_file) as f:
            counter_list = []
            for index, line in enumerate(f):
                if ' beginTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + START_TIME + '/>\n'
                elif ' duration="' in line:
                    if ' endTime="' in line:
                        line = line.split('<')[0] + '<granPeriod ' + DURATION + ' ' + END_TIME + '/>\n'
                    else:
                        line = line.split('<')[0] + '<repPeriod ' + DURATION + '/>\n'
                elif ' endTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + END_TIME + '/>\n'
                elif '<fileSender localDn="' in line:
                    SRC_TEMPLATE_TO_FIELD_MAP[template_file]['fileSender'].append(index)
                elif '<managedElement localDn="' in line:
                    SRC_TEMPLATE_TO_FIELD_MAP[template_file]['managedElement'].append(index)
                elif '<measType p="' in line:
                    counter_list.append(line.split('>')[1].split('<')[0])
                elif '<measValue measObjLdn="' in line:
                    objLdn = line.strip().replace(' ', '')
                    for counter_index, counter_name in enumerate(counter_list):
                        counter_value_index = index + 1 + counter_index
                        SRC_TEMP_MEASOBJ_COUNTER_POS_MAP[template_file][objLdn][counter_name] = counter_value_index
                    if short_fdn in line:
                        SRC_TEMPLATE_TO_FIELD_MAP[template_file]['measValue'].append(index)
                elif '</measInfo>' in line:
                    counter_list = []
                SRC_TEMPLATE_TO_DATA_MAP[template_file].append(line)
    except:
        log_statement('ERROR : Issue while fetching pm information for template {}'.format(template_file), 1)


def main(args):
    global START_TIME, END_TIME, DURATION, EBSN_PM_PATH, EBSN_DEST_FILE_FORMAT
    log_statement('INFO : Loading EBSN PM Configuration...')
    if len(args) != 10:
        help_message(1)
    try:
        opts, args = getopt.getopt(args, 'h:s:e:d:t:f:',
                                   ['help=', 'start=', 'end=', 'duration=', 'time=', 'format='])
        for opt, arg in opts:
            if opt in ('-s', '--start'):
                START_TIME = arg.strip()
            elif opt in ('-e', '--end'):
                END_TIME = arg.strip()
            elif opt in ('-d', '--duration'):
                DURATION = arg.strip()
            elif opt in ('-t', '--time'):
                if arg.strip() is None or arg.strip() == '':
                    help_message(1)
                else:
                    EBSN_PM_PATH = EBSN_PM_PATH.replace('<EPOCH>', arg.strip())
            elif opt in ('-f', '--format'):
                if arg.strip() is None or arg.strip() == '':
                    help_message(1)
                else:
                    EBSN_DEST_FILE_FORMAT = arg.strip()
        if START_TIME is None or START_TIME == '':
            help_message(1)
        if END_TIME is None or END_TIME == '':
            help_message(1)
        if DURATION is None or DURATION == '':
            help_message(1)
    except:
        help_message(1)
    move_json_files()
    if os.path.exists(EBSN_SRC_NE_TO_TOPO_NE_FILE) and os.path.exists(EBSN_SRC_ROP_INFO_FILE):
        get_source_template_for_rop_time()
        process_map = consume_parallel_processing_metadata_json()
        generate_pm_dirs()
        log_statement('INFO : EBSN PM Configuration loaded and generating PM files.')
        initiate_worker(process_map)
    else:
        log_statement(
            'ERROR : Either file {} or {} not present.'.format(EBSN_SRC_ROP_INFO_FILE, EBSN_SRC_NE_TO_TOPO_NE_FILE), 1)


if __name__ == '__main__':
    main(sys.argv[1:])

