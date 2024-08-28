#!/usr/bin/python

import sys, getopt, os
from time import time, sleep
import json

FLS_SERVICE_PORT = '8080'


json_file_path, remove_file_path, instrument_file_path = '/tmp/values.json', '/tmp/rm.json', '/tmp/instrument.json'
jar_statement = 'java -jar /netsim_users/pms/lib/fls-updator-service.jar <operation> <file_path> eric-oss-fls-enm-id ' + FLS_SERVICE_PORT


is_wait = False


def exit_script(status=0):
    sys.exit(status)


def help_message(status):
    print("Arguments :\nAddition of files to db: '-a', '--add'\nDeletion of files from db: '-d', '--delete'\nUpdate instrumentation data: '-i', '--insert'")
    exit_script(status)

def generate_reference_time():
    from datetime import datetime, timedelta
    sys_time = datetime.now()
    remainder = (sys_time.minute % 15) + 75
    reference_time = sys_time - timedelta(minutes = remainder)
    return [reference_time.strftime("%Y-%m-%dT%H:%M:00")]

def generate_timestamp_list(delta=1):
    from datetime import datetime, timedelta
    timestamp_list = []
    end_time = datetime.now() - timedelta(hours=delta)
    start_time = datetime.now() - timedelta(hours=delta+1)
    start_time = start_time.replace(minute=start_time.minute // 15 * 15, second=0)
    while start_time <= end_time:
        #2023-07-25T10:45:00
        timestamp = start_time.strftime("%Y-%m-%dT%H:%M:00")
        timestamp_list.append(timestamp)
        start_time+=timedelta(minutes=15)
    return timestamp_list

def delete_db_entries(ref_time):
    print('INFO : Deleting entries from db...')
    timestamp_deletion_list = generate_timestamp_list()
    with open(remove_file_path, 'w') as f:
        json.dump(timestamp_deletion_list, f)
    new_jar_statement = jar_statement.replace('<operation>', 'delete').replace('<file_path>', remove_file_path)
    os.system(new_jar_statement)
    print('INFO : Deletion of the following ROPS from DB: ' + str(timestamp_deletion_list) + 'completed.')


def update_intrumentation():
    print('INFO : Adding instrumentation data...')
    new_jar_statement = jar_statement.replace('<operation>', 'addInstrumentation').replace('<file_path>', instrument_file_path)
    os.system(new_jar_statement)
    print('INFO : Instrumentation added.')


def add_entry_in_db():
    print('INFO : Adding files to db...')
    new_jar_statement = jar_statement.replace('<operation>', 'add').replace('<file_path>', json_file_path)
    if is_wait:
        status = False
        max_wait_time = int(time()) + 300
        while time() < max_wait_time:
            if not os.path.isfile(json_file_path):
                sleep(5)
            else:
                status = True
                break
        if not status:
            print('ERROR : Could not add files in db due to wait timeout.')
            return
    os.system(new_jar_statement)
    print('INFO : File addition completed.')

def main():
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "a:d:i:", ['add=', 'delete=', 'instr='])
    except:
        help_message(1)
  
    for opt, arg in opts:
        if opt in ['-a', '--add']:
            if arg.lower() != 'default':
                global json_file_path, is_wait
                json_file_path = arg
                is_wait = True
            add_entry_in_db()
        elif opt in ['-d', '--delete']:
            global remove_file_path
            ref_time = generate_reference_time()
            #remove_file_path = arg
            delete_db_entries(ref_time)
        elif opt in ['-i', '--insert']:
            update_intrumentation()
        else:
            help_message(1)

if __name__ == '__main__':
    main()
