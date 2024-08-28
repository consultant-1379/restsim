#!/usr/bin/python -u
import os.path
import re
import sys

my_keywords_list = ['filter(', '/', '.iteritems()', '.iterkeys()', '.keys()[', 'print', '777', '775', '755', '555',
                    'fromsubprocess', 'gzip', 'BaseHTTPServer', 'urlparser', 'ConfigParser', 'logging.warn(',
                    '.has_key(']


def process_file_list(my_file_list):
    for my_file in my_file_list:
        if not os.path.exists(my_file) or not os.path.isfile(my_file):
            print('Skipping {}'.format(my_file))
            continue
        with open(my_file, 'r') as my_file_obj:
            print('=======================================================================================\n\n')
            print('Processing file {}...'.format(my_file))
            for index, line in enumerate(my_file_obj):
                modified_line = line.replace('\n', '').replace(' ', '').strip()
                if modified_line.startswith('#'):
                    continue
                for my_keyword in my_keywords_list:
                    if my_keyword not in modified_line:
                        continue
                    if my_keyword == 'print':
                        if 'print(' not in modified_line and 'print_' not in modified_line:
                            print('Line #{}, failing for KEYWORD {}'.format(index + 1, my_keyword))
                            print(line.replace('\n', '') + '\n')
                    elif my_keyword == '/':
                        new_modified_line = modified_line
                        extracted_data_list = re.findall(r'"([^"]*)"', new_modified_line)
                        for extracted_data in extracted_data_list:
                            new_modified_line = new_modified_line.replace(extracted_data, '')
                        extracted_data_list = re.findall(r"'([^']*)'", new_modified_line)
                        for extracted_data in extracted_data_list:
                            new_modified_line = new_modified_line.replace(extracted_data, '')
                        if '/' in new_modified_line:
                            print('Line #{}, failing for KEYWORD {}'.format(index + 1, my_keyword))
                            print(line.replace('\n', '') + '\n')
                    elif my_keyword in ['777', '775', '755', '555']:
                        if '0o' + my_keyword not in modified_line:
                            print('Line #{}, failing for KEYWORD {}'.format(index + 1, my_keyword))
                            print(line.replace('\n', '') + '\n')
                    elif my_keyword == 'gzip':
                        if 'importgzip' in modified_line:
                            continue
                        elif modified_line.split('gzip.open(')[-1].split(')')[0].split(',')[-1].strip() in ['\'wt\'',
                                                                                                            '"wt"',
                                                                                                            '\'r\'',
                                                                                                            '"r"']:
                            continue
                        else:
                            print('Line #{}, failing for KEYWORD {}'.format(index + 1, my_keyword))
                            print(line.replace('\n', '') + '\n')
                    else:
                        print('Line #{}, failing for KEYWORD {}'.format(index + 1, my_keyword))
                        print(line.replace('\n', '') + '\n')
            print('File {} processed.'.format(my_file))


def main(args):
    file_list = []
    with open(args[0], 'r') as file_list_data:
        for line in file_list_data:
            line = line.replace('\n', '').strip()
            if line.endswith('.py'):
                for my_path in ['/netsim_users/pms/bin/', '/netsim_users/auto_deploy/bin/']:
                    file_list.append(my_path + line)
    process_file_list(file_list)


if __name__ == '__main__':
    main(sys.argv[1:])
