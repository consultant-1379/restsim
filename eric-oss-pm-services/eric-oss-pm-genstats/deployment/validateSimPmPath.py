#!/usr/bin/python

import os
from _collections import defaultdict
from GenericMethods import fetchNetsimCfgParam, get_hostname

sim_data_file = '/netsim/genstats/tmp/sim_data.txt'
LOG_PATH = '/netsim_users/pms/logs/'
SIM_PM_PATH_LOG_FILE = 'sim_pm_path.log'
ne_pm_path_map = defaultdict(lambda : defaultdict(list))


def generateLogDirectory():
    if not os.path.isdir(LOG_PATH):
        try:
            os.makedirs(LOG_PATH, 0755)
        except Exception as x:
            print 'ERROR : Issue while creating ' + LOG_PATH
            print str(x)


def sortNePmPathMap(dep):
    global ne_pm_path_map
    f_o = None
    try:
        f_o = open(LOG_PATH + SIM_PM_PATH_LOG_FILE, 'a')
        for ne, pm_path_map in ne_pm_path_map.iteritems():
            for dir_type, path_list in pm_path_map.iteritems():
                unique_list = list(set(path_list))
                if len(unique_list) > 1:
                    message = None
                    if dep == 'NSS':
                        message = 'WARNING : Multiple ' + dir_type + ' path found, node type ' + ne + ' : [' + ', '.join(unique_list) + '].'
                    else:
                        message = 'ERROR : Multiple ' + dir_type + ' path found, node type ' + ne + ' : [' + ', '.join(unique_list) + '].\nPlease check ' + sim_data_file + ' file for node type and contact SIMNET team to resolve the issue.'
                    print message
                    f_o.write(message + '\n')
                    f_o.flush()
    except Exception as x:
        print str(x)
    finally:
        f_o.close()


def generateNePmPathMap(cfg):
    global ne_pm_path_map
    with open(sim_data_file, 'r') as fin:
        for line in fin:
            lineElements = line.split()
            node_type, stats_dir, trace_dir = lineElements[5], lineElements[9], lineElements[11]
            ne_pm_path_map[node_type]['STATS'].append(stats_dir)
            ne_pm_path_map[node_type]['TRACE/EVENTS'].append(trace_dir)
    if ne_pm_path_map:
        deployment = fetchNetsimCfgParam('TYPE').replace('"','')
        sortNePmPathMap(deployment)


def main():
    if os.path.isfile(sim_data_file):
        generateLogDirectory()
        netsim_conf_file = '/tmp/' + get_hostname()
        if os.path.isfile(netsim_conf_file):
            generateNePmPathMap(netsim_conf_file)
    

if __name__ == '__main__':
    main()
