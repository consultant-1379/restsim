#!/usr/bin/python

################################################################################
# COPYRIGHT Ericsson 2018
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 20.12
# Purpose       :  Purpose of this script is to map the RNC cells in Template file
# Jira No       :  NSS-35121
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/10100812
# Description   :  NRM5.1 10K WCDMA network in NSS
# Date          :  05/07/2021
# Last Modified :  kumar.dhiraj7@tcs.com
####################################################

from _collections import defaultdict
import sys, os

from DataAndStringConstants import SIM_DATA_FILE, NETSIM_DIR
from confGenerator import getCurrentDateTime
from utilityFunctions import Utility

utils = Utility()

NRM_TYPE = utils.getDeploymentVersionInformation(utils.getHostName())
RNC_CONFIGURATION = {0 : [1, 2, 3, 5, 7], 1 : [4, 6, 8, 9, 10], 2 : [11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20]}
rncCellMap = defaultdict(list)
READ_MODE, WRITE_MODE = 'r', 'w'
error, warn, info = 'ERROR', 'WARNING', 'INFO'
rncCellValueList = []

if NRM_TYPE == 'NRM5':
    RNC_CONFIGURATION = {0 : [5, 7], 1 : [1, 2, 6, 8, 9, 10], 2 : [3, 11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20]}
elif NRM_TYPE == 'NRM5.1':
    RNC_CONFIGURATION = {0 : [5, 7], 1 : [1, 2, 4, 6, 8, 9, 10], 2 : [11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20], 5: [3]}
def isFileExists(inFile):
    """
        This is a generic method which return True/False based on file exist/not exists.
    """
    if os.path.isfile(inFile):
        return True
    return False


def findRncSimNameUsingMimFile(inMimFile):
    """
        This method is responsible to provide the list of RNC simulation present in sim_data.txt file, which are matching with
        provided input mim file name.
    """
    rncList = []
    with open(SIM_DATA_FILE, READ_MODE) as sim_data:
        for data in sim_data:
            elements = data.split()
            if elements[1].split('-')[-1].startswith('RNC') and elements[5] == 'RNC' and elements[13] == inMimFile:
                rncList.append(elements[1])
    return rncList


def createUtranCellMap(inputSim):
    """
        This method will create the UtranCell file path based on input RNC sims and gather the data from that file and will create the map.
        rncCellMap <MAP> = { RNC_SIM_ID : ['Cell_1','Cell_2',...] }
    """
    utranCellFilePath = NETSIM_DIR + inputSim + '/SimNetRevision/UtranCell.txt'
    if isFileExists(utranCellFilePath):
        global rncCellMap
        simId = inputSim.split('-')[-1]
        with open(utranCellFilePath, READ_MODE) as inCellFile:
            for data in inCellFile:
                rncCellMap[simId].append(''.join(data.split()).split(',')[-1].split('=')[-1])
        if not rncCellMap.has_key(simId):
            return inputSim
    else:
        return inputSim
    return None


def processRncSimList(inputList):
    """
        This method will iterate on input RNC sim list.
    """
    emptyRncDataList = []
    for sim in inputList:
        emptyRncDataList.append(createUtranCellMap(sim))
    return filter(None, emptyRncDataList)


def fetchRequiredRncCellId(rncId):
    """
        This method returns the required cell count for provided RNC sim.
    """
    simId = rncId.replace('RNC', '')
    if simId.isdigit() and '.' not in simId:
        simId = int(simId)
        if simId == 4 and NRM_TYPE == 'NRM5':
            return int(rncCellValueList[4])
        if simId > 20:
            return int(rncCellValueList[4])
        for type, ids in RNC_CONFIGURATION.iteritems():
            for id in ids:
                if id == simId:
                    return int(rncCellValueList[type])
        throwConsoleLogs(error, 'Invalid RNC sim id for sim: ' + rncId)
    else:
        throwConsoleLogs(error, 'RNC simid not present in sim name: ' + rncId)
                    

def logForSimnetTeam():
    return 'Why to worry, please contact SIMNET TEAM.'

                  
def correctRncTemplateFiles(inTemplate):
    """
        This method takes template as an input and creates new Template with mapping RNC cells in MO.
    """
    if isFileExists(inTemplate):
        inTemplateObj = open(inTemplate, READ_MODE)
        for rncId in rncCellMap.iterkeys():
            newRncTemplate = inTemplate.replace('.xml', '_' + rncId + '.xml')
            rncCellList = rncCellMap[rncId]
            rncCellListLen = len(rncCellList) 
            if rncCellListLen < fetchRequiredRncCellId(rncId):
                throwConsoleLogs(warn, 'Sufficient RNC cells not present in UtranCell file for RNC sim: ' + rncId + '. ' + logForSimnetTeam())
            with open(newRncTemplate, WRITE_MODE) as outTemplate:
                for line in inTemplateObj:
                    preDefUtranId = ''
                    """ Checking line data for UtranCell MO present in it or not, if present map the RNC cell or leave it as it is. """
                    if line.startswith('<moid>') and ',UtranCell=' in line:
                        preDefUtranId = int(line.replace('<moid>', '').replace('</moid>', '').split(',UtranCell=')[-1].split(',')[0])
                        if rncCellListLen >= preDefUtranId:
                            line = line.replace(',UtranCell=' + str(preDefUtranId), ',UtranCell=' + rncCellList[preDefUtranId - 1])
                    outTemplate.write(line)
                    outTemplate.flush()
            inTemplateObj.seek(0)   
        inTemplateObj.close()
    else:
        throwConsoleLogs(error, 'Template file ' + inTemplate + ' not present.')


def throwConsoleLogs(_status, _message):
    """
        This is generic method for throwing console logs.
    """
    print getCurrentDateTime() + ' ' + _status + ': ' + _message
    if _status == 'ERROR':
        sys.exit(1)


def main(argv):
    """
        Main Method
    """
    if argv[2]:
        global rncCellValueList
        rncCellValueList = argv[2].split(':')
    else:
        throwConsoleLogs(error, 'Not able to get RNC Cell Configuration.')

    if isFileExists(SIM_DATA_FILE):
        rncSimList = findRncSimNameUsingMimFile(argv[0])
        if rncSimList:
            errorSimList = processRncSimList(rncSimList)
            if errorSimList:
                throwConsoleLogs(error, 'Either UtranCell data not present in file or UtranCell data file not present for RNC sim(s) : ' + ', '.join(errorSimList) + '. ' + logForSimnetTeam())
        else:
            throwConsoleLogs(error, 'RNC sims not found in ' + SIM_DATA_FILE)
        correctRncTemplateFiles(argv[1])
    else:
        throwConsoleLogs(error, SIM_DATA_FILE + ' file not present.')
        

if __name__ == '__main__':
    """ 
        Input Args : ['rncCellMapper.py', 'mim_file_name', 'template_file_with_path', 'RNC cell # based on type by : separated']
    """
    main(sys.argv[1:])

