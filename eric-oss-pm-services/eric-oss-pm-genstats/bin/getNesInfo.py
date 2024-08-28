#!/usr/bin/python -u

'''
Created on August 14, 2023

@author: xmanabh
'''
import os
import sys

EBSN_REPLAY_FOLDER = '/netsim_users/pms/xml_templates/replay/'
EBSN_REPLAY_NF_LIST = ['CUCP', 'CUUP', 'DU']
SUPPORTED_NES = ['EBSN_REPLAY']

node_type = ''


def get_file_list(folder_list, extension_list=None):
    file_list = []
    for folder in folder_list:
        for file in filter(None, os.listdir(folder)):
            if extension_list is None:
                file_list.append(file)
            else:
                for ext in extension_list:
                    if file.endswith(ext):
                        file_list.append(file)
                        break
    return list(set(file_list))


def process_fdn_for_ebsn_replay(f_list, ne_key='EBSN_REPLAY'):
    final_map = {ne_key: {'ne_count': 0, 'ne_list': []}}
    if len(f_list) > 0:
        fdn_list = []
        for f in f_list:
            fdn_name = f.split('_')[1]
            if fdn_name not in fdn_list:
                fdn_list.append(fdn_name)
                final_map[ne_key]['ne_list'].append(fdn_name)
        final_map[ne_key]['ne_count'] += len(fdn_list)
    return final_map


def get_ne_count_for_ebsn_replay():
    folder_list = [EBSN_REPLAY_FOLDER + x for x in EBSN_REPLAY_NF_LIST]
    file_list = get_file_list(folder_list, ['.xml'])
    return process_fdn_for_ebsn_replay(file_list)


def process_ne():
    if node_type == 'EBSN_REPLAY':
        return get_ne_count_for_ebsn_replay()


def main(args):
    if len(args) == 1:
        if args[0].strip().upper() in SUPPORTED_NES:
            global node_type
            node_type = args[0].strip().upper()
            print(process_ne())
        else:
            print('ERROR : Non-supported node type {} given'.format(args[0]))
    else:
        print('ERROR : Invalid number of arguments given.')


if __name__ == '__main__':
    main(sys.argv[1:])

