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
# Version no    :  NSS 18.13
# Purpose       :  This script is responsible for finding out the counter volume in given PM file, with the help of counter property file.
# Jira No       :  NSS-19876
# Gerrit Link   :  
# Description   :  This script is responsible for finding out the counter volume in given PM file, with the help of counter property file.
# Date          :  17/07/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

import os, sys, gzip
from _collections import defaultdict

pmFileName, counterPropFile, node_type = None, None, None
err, info, warn = 'ERROR', 'INFO', 'WARNING'
READ_MODE, WRITE_MODE = 'r', 'w'
supported_node_type = ['ECIM', 'CPP']
SINGLE_VALUE = 1
MULTI_VALUE = 2
PDF_VALUE = 3
counterPropMap = defaultdict(lambda : defaultdict())

def findCounterType(inLine):
    lineElements = inLine.strip().split(',')
    mo_name, counter_name, counter_type = lineElements[0], lineElements[1], lineElements[3]
    if counter_type == 'SINGLE_VALUE':
        counter_type = SINGLE_VALUE
    elif counter_type == 'MULTI_VALUE':
        if lineElements[4] == 'UNCOMPRESSED':
            counter_type = MULTI_VALUE
        elif lineElements[4] == 'COMPRESSED':
            counter_type = PDF_VALUE
        else:
            throwConsoleLogs(err, 'Invalid Multi-value type Counter found : ' + counter_name)
    else:
        throwConsoleLogs(err, 'Invalid Counter type found : ' + counter_name)
    return mo_name, counter_name, counter_type


def readCounterPropertyFile():
    global counterPropMap
    with open(counterPropFile, READ_MODE) as inProp:
        for line in inProp:
            mo_name, counter_name, counter_type = findCounterType(line)
            if mo_name not in counterPropMap.keys():
                counterPropMap[mo_name][counter_name] = counter_type
            else:
                if counter_name not in counterPropMap[mo_name].keys():
                    counterPropMap[mo_name][counter_name] = counter_type
                else:
                    throwConsoleLogs(warn, 'Possible Multi-parent scenario for MO-Counter : ' + line + ', which can alter counter volume.')


def returnMoVolume(mo, cntList, cntValList):
    moCounterVolume = 0
    for index, name in enumerate(cntList):
        if mo in counterPropMap.keys():
            if name in counterPropMap[mo].keys():
                cnt_type = counterPropMap[mo][name]
                data = cntValList[index]
                if cnt_type == SINGLE_VALUE:
                    moCounterVolume += 1
                elif cnt_type == MULTI_VALUE:
                    moCounterVolume += len(data.split(','))
                elif cnt_type == PDF_VALUE:
                    moCounterVolume += (len(data.split(','))//2)
                else:
                    throwConsoleLogs(err, 'Invalid counter type ' + cnt_type + ' found while calculating counter volume.')
            else:
                throwConsoleLogs(err, 'Counter name ' + name + ' not found in counter property file, which is present in PM file for MO : ' + mo)
        else:
            throwConsoleLogs(err, 'MO ' + mo + ' not found in counter property file, which is present in PM file.')
    return moCounterVolume


def readCppData(content):
    mo_tag, counter_tag, counter_value_tag = '<moid>', '<mt>', '<r>'
    counterList = []
    counterValList = []
    counterVolume = 0
    mo_name = None
    initCheck = 'start'
    for line in content:
        lineCpy = line.strip()
        if lineCpy.startswith(counter_tag):
            if initCheck == 'end':
                counterVolume += returnMoVolume(mo_name, counterList, counterValList)
                del counterList[:]
                del counterValList[:]
                mo_name = None
                initCheck = 'start'
            counterList.append(lineCpy.split('>')[1].split('<')[0])
            continue
        if lineCpy.startswith(mo_tag):
            if counterList:
                mo_name = lineCpy.split('=')[-2].split(',')[-1]
            else:
                throwConsoleLogs(err, 'No counters present for MO : ' + lineCpy)
            continue
        if lineCpy.startswith(counter_value_tag):
            if initCheck != 'end':
                initCheck = 'end'
            data = lineCpy.split('>')[1].split('<')[0]
            if not data:
                data = '0'
            counterValList.append(data)
    counterVolume += returnMoVolume(mo_name, counterList, counterValList)
    throwConsoleLogs(info, 'Total Counter Volume in PM file is : ' + str(counterVolume))
    

def readEcimData(content):
    mo_tag, counter_tag, counter_value_tag = '<measValue measObjLdn=', '<measType p=', '<r p='
    mo_name = None
    counterList = []
    counterValList = []
    counterVolume = 0
    initCheck = 'start'
    for line in content:
        lineCpy = line.strip()
        if lineCpy.startswith(counter_tag):
            if initCheck == 'end':
                counterVolume += returnMoVolume(mo_name, counterList, counterValList)
                del counterList[:]
                del counterValList[:]
                initCheck = 'start'
                mo_name = None
            counterList.append(lineCpy.split('>')[1].split('<')[0])
            continue
        if lineCpy.startswith(mo_tag):
            mo_name = lineCpy.split(',')[-1].split('=')[0]
            continue
        if lineCpy.startswith(counter_value_tag):
            if initCheck != 'end':
                initCheck = 'end'
            data = lineCpy.split('>')[1].split('<')[0]
            if not data:
                data = '0'
            counterValList.append(data)
    counterVolume += returnMoVolume(mo_name, counterList, counterValList)
    throwConsoleLogs(info, 'Total Counter Volume in PM file is : ' + str(counterVolume)) 


def calculateCounterVolumeFromPmFile():
    inPmContent = gzip.open(pmFileName, READ_MODE)
    if node_type == 'CPP':
        readCppData(inPmContent)
    else:
        readEcimData(inPmContent)
    inPmContent.close()


def checkFileExistance(fileName):
    if not os.path.isfile(fileName):
        throwConsoleLogs(err, 'File ' + fileName + ' not found.')
    

def throwConsoleLogs(status, msg):
    print (status + ': ' + msg)
    if status == 'ERROR':
        sys.exit(1)

        
def readGivenArgs(args):
    global pmFileName, counterPropFile, node_type
    pmFileName, counterPropFile, node_type = args[0], args[1], args[2].upper()
    checkFileExistance(pmFileName)
    checkFileExistance(counterPropFile)
    if node_type not in supported_node_type:
        throwConsoleLogs(err, 'Improper node type given : ' + node_type)
    
        
def main(argv):
    readGivenArgs(argv)
    readCounterPropertyFile()
    calculateCounterVolumeFromPmFile()


if __name__ == '__main__':
    main(sys.argv[1:])
