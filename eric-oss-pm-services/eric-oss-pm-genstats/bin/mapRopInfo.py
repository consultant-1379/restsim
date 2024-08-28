#!/usr/bin/python -u

# Created on September 19, 23 by @xmanabh

import getopt
import gzip
import json
import os.path
import sys
from collections import defaultdict

ne_type = ''
source_template, destination_template = '', ''
start_time, end_time, duration = '', '', ''

json_map = None

DEBUG = True
enable_mapping = False

SUPPORTED_NE_TYPES = ['EBSN_REPLAY']


def terminate_script(status=0):
    sys.exit(status)


def help_message(status=0):
    print('ERROR : Invalid arguments given.')
    print(
        'INFO : Calling arguments >> python <script_name>.py -n <ne_type> -o <source_file> -f <dest_file> -s <start_time> -e <end_time> -d <duration>')
    terminate_script(status)


def check_mapping_conditions(fdn, begin_time):
    meas_obj_ldn_to_counter_map = defaultdict(list)
    if fdn not in json_map:
        return False, None
    for meas_obj_ldn_key, begin_time_map in json_map[fdn].items():
        if begin_time in begin_time_map:
            meas_obj_ldn_to_counter_map[meas_obj_ldn_key].extend(json_map[fdn][meas_obj_ldn_key][begin_time].keys())
    if len(meas_obj_ldn_to_counter_map.keys()) > 0:
        if DEBUG:
            print('INFO : Mapping of {} Meas Obj Ldn found for destination file {}.'.format(
                len(meas_obj_ldn_to_counter_map.keys()), destination_template))
        return True, meas_obj_ldn_to_counter_map
    return False, None


def generate_file_with_mapping(fdn, begin, json_meas_to_counter_map):
    this_meas_counter_mapping = False
    counter_to_index, index_to_value = {}, {}
    file_descriptor = None
    try:
        file_descriptor = gzip.open(destination_template, 'wt')
        with open(source_template, 'r') as f:
            for line in f:
                if 'beginTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + start_time + '/>\n'
                elif 'duration="' in line:
                    if 'endTime="' in line:
                        line = line.split('<')[0] + '<granPeriod ' + duration + ' ' + end_time + '/>\n'
                    else:
                        line = line.split('<')[0] + '<repPeriod ' + duration + '/>\n'
                elif 'endTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + end_time + '/>\n'
                elif '<measInfo>' in line or '<measInfo ' in line:
                    counter_to_index.clear()
                elif '</measValue>' in line:
                    index_to_value.clear()
                elif '<measType p="' in line:
                    counter_to_index[line.split('>')[1].split('<')[0]] = line.split('"')[1]
                elif '<measValue measObjLdn="' in line:
                    meas_obj = line.split('"')[1]
                    if meas_obj in json_meas_to_counter_map:
                        this_meas_counter_mapping = True
                        for counter in json_meas_to_counter_map[meas_obj]:
                            if counter in counter_to_index:
                                index_to_value[counter_to_index[counter]] = json_map[fdn][meas_obj][begin][counter]
                    else:
                        this_meas_counter_mapping = False
                elif '<r p="' in line:
                    if this_meas_counter_mapping:
                        counter_index = line.split('"')[1]
                        if counter_index in index_to_value:
                            line = line.split('>')[0] + '>' + index_to_value[counter_index] + '</r>\n'
                file_descriptor.write(line)
    except Exception as e:
        print('ERROR : Issue while generating file {}.'.format(destination_template))
        print(e)
    finally:
        if file_descriptor is not None:
            file_descriptor.flush()
            file_descriptor.close()


def generate_file_without_mapping():
    file_descriptor = None
    try:
        file_descriptor = gzip.open(destination_template, 'wt')
        with open(source_template, 'r') as f:
            for line in f:
                if 'beginTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + start_time + '/>\n'
                elif 'duration="' in line:
                    if 'endTime="' in line:
                        line = line.split('<')[0] + '<granPeriod ' + duration + ' ' + end_time + '/>\n'
                    else:
                        line = line.split('<')[0] + '<repPeriod ' + duration + '/>\n'
                elif 'endTime="' in line:
                    line = line.split('<')[0] + '<measCollec ' + end_time + '/>\n'
                file_descriptor.write(line)
    except Exception as e:
        print('ERROR : Issue while generating file {}.'.format(destination_template))
        print(e)
    finally:
        if file_descriptor is not None:
            file_descriptor.flush()
            file_descriptor.close()


def generate_information():
    if os.path.exists(source_template) and os.path.isfile(source_template):
        if enable_mapping:
            file_base_name = os.path.basename(destination_template).replace('.xml.gz', '').replace('.xml', '')
            fdn_key = '_'.join(file_base_name.split('_')[1:])
            begin_time_key = file_base_name[:19].split('.')[-1]
            do_mapping, meas_obj_ldn_to_counter_map = check_mapping_conditions(fdn_key, begin_time_key)
            if do_mapping:
                generate_file_with_mapping(fdn_key, begin_time_key, meas_obj_ldn_to_counter_map)
            else:
                generate_file_without_mapping()
        else:
            generate_file_without_mapping()
    else:
        print('ERROR : Given source template {} does not found or not a file.'.format(source_template))
        terminate_script(1)


def consume_json_mapping(json_file):
    global json_map, enable_mapping
    try:
        if os.path.exists(json_file) and os.path.isfile(json_file):
            with open(json_file, 'r') as jsf:
                json_map = json.load(jsf)
            if len(json_map.keys()) > 0:
                enable_mapping = True
    except Exception as e:
        json_map = None
        pass


def main(args):
    global ne_type, source_template, destination_template, start_time, end_time, duration
    mapping_file = ''
    try:
        opts, args = getopt.getopt(args, 'h:n:o:f:s:e:d:m:',
                                   ['help=', 'ne=', 'origin=', 'final=', 'start=', 'end=', 'duration=', 'map='])
        for opt, arg in opts:
            if opt in ('-n', '--ne'):
                if arg.upper() in SUPPORTED_NE_TYPES:
                    ne_type = arg.upper()
                else:
                    print('ERROR : Invalid ne type {} given.'.format(arg))
                    terminate_script(1)
            elif opt in ('-o', '--origin'):
                source_template = arg.strip()
            elif opt in ('-f', '--final'):
                destination_template = arg.strip()
            elif opt in ('-s', '--start'):
                start_time = arg.strip()
            elif opt in ('-e', '--end'):
                end_time = arg.strip()
            elif opt in ('-d', '--duration'):
                duration = arg.strip()
            elif opt in ('-m', '--map'):
                mapping_file = arg.strip()
            else:
                help_message(1)
    except:
        help_message(1)
    if mapping_file != '':
        consume_json_mapping(mapping_file)
    generate_information()
    terminate_script(0)


if __name__ == '__main__':
    main(sys.argv[1:])
