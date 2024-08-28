#!/usr/bin/python

from utilityFunctions import Utility
import sys
from _collections import defaultdict

u = Utility()

nodeToMimMap = defaultdict(list)


def exitScript():
    u.printStatements('Mim version validation completed.', 'INFO')
    sys.exit()
    

def validateSimulationMimVersion():
    with open(u.sim_data_file, 'r') as f:
        for line in f:
            if line:
                lineElements = line.split()
                sim_name, node_type, mim_version = lineElements[1].strip(), lineElements[5].strip(), lineElements[7].strip()
                if 'MSRBS-V2' in node_type and 'LTE' not in sim_name.split('-')[-1]:
                    continue
                if node_type == 'RNC' or node_type == 'RBS':
                    continue
                if node_type in nodeToMimMap:
                    if mim_version not in nodeToMimMap[node_type]:
                        u.printStatements('Simulation ' + sim_name + ' having mim version ' + mim_version + ' has been supported through default MO configuration.', 'WARNING')


def generateNodeToMimVersionMapping(mo_file):
    global nodeToMimMap
    with open(mo_file, 'r') as f:
        next(f)
        for line in f:
            line = line.strip()
            if line and line[0].isalnum():
                lineElements = line.split(',')
                nodeToMimMap[lineElements[0]].append(lineElements[1])


def getMoCfgFileName(r, c):
    mo_cfg = '/netsim_users/reference_files/' + r + '/mo_cfg_' + c + '.csv'
    if u.checkFileExistance(mo_cfg):
        return mo_cfg
    else:
        u.printStatements('MO CFG ' + mo_cfg + ' not found.' , 'ERROR')
        exitScript()


def preValidations():
    if u.checkFileExistance(u.netsim_cfg) and u.checkFileExistance(u.sim_data_file):
        release = u.getDeploymentVersionInformation()
        if release:
            if release.startswith('NRM'):
                counter_volume = u.getRequiredCounterVolumeInformation()
                if counter_volume:
                    return release, counter_volume
                else:
                    u.printStatements('Counter volume parameter value can not be empty.', 'ERROR')
                    exitScript()
            else:
                u.printStatements('Mim version validation not required for Deployment release ' + release + '.', 'INFO')
                exitScript()
        else:
            u.printStatements('Deployment release can not be empty.' , 'ERROR')
            exitScript()
    else:
        u.printStatements('Either ' + u.netsim_cfg + ' or ' + u.sim_data_file + ' not present.', 'ERROR')
        exitScript()


def main():
    u.printStatements('Checking mim version support for deployed Simulations.', 'INFO')
    release, counter_volume = preValidations()
    generateNodeToMimVersionMapping(getMoCfgFileName(release, counter_volume))
    validateSimulationMimVersion()
    exitScript()
    

if __name__ == '__main__':
    main()
