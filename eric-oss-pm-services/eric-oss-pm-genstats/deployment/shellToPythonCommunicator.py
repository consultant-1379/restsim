#!/usr/bin/python
import sys
import os

from utilityFunctions import Utility

u = Utility()


def exitScript(msg, msg_type, status):
    u.printStatements(msg, msg_type)
    sys.exit(status)
    

def getNratPmPathData(sim_name):
    try:
        json_data = u.getJsonMapObjectFromFile(u.celltrace_json)
        if json_data:
            for key in json_data.keys():
                if sim_name == key.split('|')[0]:
                    if json_data[key]:
                        return ' '.join(json_data[key])
                    else:
                        exitScript('Simulation ' + sim_name + ' data not present in ' + u.celltrace_json + ' file.', 'ERROR', 1)
            exitScript('Simulation name ' + sim_name + ' not present in ' + u.celltrace_json + ' file.', 'ERROR', 1)
        else:
            exitScript('No data available for uetrace in file ' + u.celltrace_json, 'ERROR', 1)
    except Exception as e:
        sys.exit(1)
    return None


def processArguments(args_list):
    code = int(args_list[0])
    if code == 1:
        print (getNratPmPathData(args_list[1]))


def main(argument_list):
    processArguments(argument_list)


if __name__ == '__main__':
    main(sys.argv[1:])
