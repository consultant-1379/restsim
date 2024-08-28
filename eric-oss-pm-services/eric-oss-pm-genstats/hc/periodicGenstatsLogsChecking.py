#!/usr/bin/python

import os
import sys
from datetime import datetime, timedelta

logs_dir = '/netsim_users/pms/logs/'
netsim_cfg = '/netsim/netsim_cfg'
info = 'INFO: '
err = 'ERROR: '
warn = 'WARNING: '
rv_interval = 15


def getCurrentDateTime():
    """ return system's current time"""
    return str(datetime.today().replace(microsecond=0))


def logging(msg, type):
    """ Logging method"""
    if type == err:
        print getCurrentDateTime() + ' ' + type + msg
        sys.exit(1)
    else:
        print getCurrentDateTime() + ' ' + type + msg


def validate_logs(file, start_time):
    """ Validation logic for logs checking """
    err_logs = []
    find_start = False
    with open(logs_dir + file, 'r') as f:
        for line in f:
            line = line.strip()
            if start_time in line and 'Start' in line:
                find_start = True
                break
        if find_start:
            for line in f:
                line = line.strip()
                if 'ERROR' in line.upper():
                    err_logs.append(line)
        else:
            logging('Skipping ' + logs_dir + file + ' file checking as starting point not found.', info)
    if err_logs:
        logging('Found ' + str(len(err_logs)) + ' ERROR(s) in ' + logs_dir + file + ' file in between ' + start_time + ':00 and ' + getCurrentDateTime() + ' time.', info)
    del err_logs[:]


def get_interval_info():
    """ get and validate value of periodic interval from netsim cfg and return in minutes value.
    """
    attr = 'PERIODIC_HC_INTERVAL='
    if not os.path.isfile(netsim_cfg):
        logging(netsim_cfg + ' file not present. Exiting process.', err)
        sys.exit(1)
    with open(netsim_cfg, 'r') as f:
        for line in f:
            if line.startswith(attr):
                value = str(line.split('=')[1].replace('"', '').strip())
                value = value.upper()
                if 'M' in value:
                    value = int(value.replace('M', ''))
                    if value == 0:
                        return 60
                    else:
                        return value
                elif 'H' in value:
                    value = int(value.replace('H', ''))
                    if value == 0 or value == 24:
                        return 1440
                    else:
                        return (value * 60)
                else:
                    logging('Invalid value provided in ' + attr.split('=')[0] + ' parameter. Exiting process.', err)
        logging('Parameter ' + attr.split('=')[0] + ' is not present. Exiting process.', err)


def get_rounded_time(now):
    """ Subtract 15 minute or remainder minute from system's local time and return it back
    """
    reminder_minute = (now.minute % rv_interval)
    if reminder_minute > 0:
        new = now - timedelta(minutes=reminder_minute)
    else:
        new = now - timedelta(minutes=rv_interval)
    return new


def main():
    """ Calling for other methods and listing files from directory."""
    delta = get_interval_info()
    mod = delta / rv_interval
    start_time = datetime.today().replace(microsecond=0).replace(second=0)
    logs_file_list = ['playbacker', 'genStats', 'genRbsGpeh', 'genGPEH', 'lte_rec', 'wran_rec']
    for i in range(0, mod):
        start_time = get_rounded_time(start_time)

    start_time = str(start_time)[:-3]

    if os.path.isdir(logs_dir):
        for file in filter(None, os.listdir(logs_dir)):
            if os.path.isfile(os.path.join(logs_dir, file)):
                if any(name.upper() in file.upper() for name in logs_file_list):
                    logging('Checking log file : ' + file, info)
                    validate_logs(file, start_time)
    else:
        logging('Directory ' + logs_dir + ' not present. Exiting process.', warn)

if __name__ == '__main__':
    main()
