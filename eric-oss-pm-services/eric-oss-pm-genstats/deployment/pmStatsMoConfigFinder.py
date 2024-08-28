#!/usr/bin/python

import sys
import os
import glob

isLTE = False
simulation_name = ""
sim_id = ""
finalNodeCellMap = {}
sim_data_file = '/netsim/genstats/tmp/sim_data.txt'
node_type = ""
mim_version = ""
mo_file = ""
moInstancesInMoCfg = []
eutranIncreament = 40
utranIncreament = 10


def findNodeCellRatio():
    nodesBasedOnUniqueCellMap = {}
    eutranCellDataFile = '/netsim/netsimdir/' + simulation_name + '/SimNetRevision/EUtranCellData.txt'
    
    if os.path.isfile(eutranCellDataFile):
        nodeCellList = []
        with open(eutranCellDataFile, 'r') as f:
            for line in f:
                if not line.startswith('#'):
                    nodeCellList.append(line.split('=')[-1])

        nodeCellList = list(set(nodeCellList))
        nodeCellRatioMap = {}

        for data in nodeCellList:
            node_name = data.split('-')[0]
            if node_name in nodeCellRatioMap:
                nodeCellRatioMap[node_name] += 1
            else:
                nodeCellRatioMap[node_name] = 1

        for node_name, no_of_cell in nodeCellRatioMap.iteritems():
            if no_of_cell not in nodesBasedOnUniqueCellMap:
                nodesBasedOnUniqueCellMap[no_of_cell] = [node_name, 1]
            else:
                instance = nodesBasedOnUniqueCellMap[no_of_cell][1]
                nodesBasedOnUniqueCellMap[no_of_cell] = [nodesBasedOnUniqueCellMap[no_of_cell][0], instance + 1]
        
        checForStartedNodes(nodesBasedOnUniqueCellMap)
    
    else:
        print 'ERROR : ' + eutranCellDataFile + ' file not exist.'
        sys.exit()
    
    return nodesBasedOnUniqueCellMap
                

def checForStartedNodes(inputMap):
    startedNodeFile = '/tmp/showstartednodes.txt'
    errorFound = False
    
    if os.path.isfile(startedNodeFile):
        findString = '/netsim/netsimdir/' + simulation_name
        
        nodeList = []
        
        with open(startedNodeFile, 'r') as f:
            for line in f:
                if findString in line:
                    nodeList.append(line.strip().split(' ')[0])
        
        nodeList = list(set(nodeList))
        
        for key, value in inputMap.iteritems():
            if value[0] in nodeList:
                nodePath = '/pms_tmpfs/' + simulation_name + '/' + value[0] + '/c/pm_data'
                if isLTE:
                    nodePath = '/pms_tmpfs/' + sim_id + '/' + value[0] + '/c/pm_data'
                
                if not os.path.isdir(nodePath):
                    print 'ERROR : ' + nodePath + ' directory not found for started node ' + value[0] + '.'
                    errorFound = True
                    
            else:
                print 'ERROR : ' + value[0] + ' node not started.'
                errorFound = True
        
        if errorFound:
            print 'ERROR : Please resolve error first and re run the script again.'
            sys.exit()
            
    else:
        print 'ERROR : ' + startedNodeFile + ' file not exists.'
        sys.exit()
    

def printCellRatio():
    cellList = sorted(finalNodeCellMap.keys())
    for cell in cellList:
        print 'No of Cell ' + str(cell) + ' : Node Instance ' + str(finalNodeCellMap[cell][1]) 


def takeInputFromUserForFileSize():
    required_avg_file_size = 180
    min_range = required_avg_file_size - 1
    max_range = required_avg_file_size + 1
    cellList = sorted(finalNodeCellMap.keys())
    valueMap = {}
    """
        valueMap = { no_of_cell : [ required_file_size, node_name ] }
    """
    goAheadFlag = False
    while True:
        for i in cellList:
            valueMap[i] = [float(int(raw_input("Please provide file size preference for " + str(i) + " cell node : ")) * 1.0), finalNodeCellMap[i][0]]
        
        average = 0.0
        count = 0
        for i in cellList:
            average += (valueMap[i][0] * finalNodeCellMap[i][1])
            count += finalNodeCellMap[i][1]
        average = (average / count)
        
        if average > min_range and average < max_range:
            print 'INFO : Average file size ' + str(average) + ' is matching with expectation. Starting to find MO configuration based on cells.'
            repeatAsking = (raw_input("Do you satisfied with average file size, press Y/y or if not press N/n : ")).lower()
            while True:
                if repeatAsking == 'y' or repeatAsking == 'n':
                    if repeatAsking.lower() == 'n':
                        break
                    else:
                        goAheadFlag = True
                        break
                else:
                    repeatAsking = (raw_input("Please provide input in form of Y/y or N/n : ")).lower()
            if goAheadFlag:
                break 
        else:
            print 'WARNING :  Average file size ' + str(average) + ' is not meeting with expectation. Please re-enter the file size value again with different combination.'
            continue
    
    return valueMap


def findAdditionalInformationForSimulation():
    global node_type, mim_version
    if os.path.isfile(sim_data_file):
        with open(sim_data_file, 'r') as f:
            for line in f:
                line = line.split()
                if simulation_name == line[1]:
                    node_type = line[5]
                    mim_version = line[7]
                    return
            print 'ERROR :  Simulation ' + simulation_name + ' not found in ' + sim_data_file + '.'
            sys.exit()
    else:
        print 'ERROR : ' + sim_data_file + ' not present.'
        sys.exit()


def findMoFile():
    deployment, cnt_volume = "", ""
    netsim_cfg = '/netsim/netsim_cfg'
    if os.path.isfile(netsim_cfg):
        with open(netsim_cfg, 'r') as f:
            for line in f:
                if line.startswith('TYPE='):
                    deployment = line.split('"')[1]
                if line.startswith('REQUIRED_COUNTER_VOLUME='):
                    cnt_volume = line.split('"')[1]
            return deployment + '/mo_cfg_' + cnt_volume + '.csv'
    else:
        print 'ERROR : ' + netsim_cfg + ' not present.'
        sys.exit()


def loadOriginalMoInstancesFromMoCfg():
    global moInstancesInMoCfg
    if os.path.isfile(mo_file):
        with open(mo_file, 'r') as f:
            for line in f:
                moInstancesInMoCfg.append(line.strip())
            moInstancesInMoCfg = filter(None, moInstancesInMoCfg)
    else:
        print 'ERROR : ' + mo_file + ' not found.'
        sys.exit()


def setNewInstances(map, pref, cellIndex):
    eutranValList = map[node_type + ',' + mim_version]['EUtranCellRelation']
    utranValList = map[node_type + ',' + mim_version]['UtranCellRelation']
    if pref.lower() == 'increase':
        eutranValList[cellIndex] = str(int(eutranValList[cellIndex]) + eutranIncreament)
        utranValList[cellIndex] = str(int(utranValList[cellIndex]) + utranIncreament)
    else:
        eutranValList[cellIndex] = str(int(eutranValList[cellIndex]) - eutranIncreament)
        utranValList[cellIndex] = str(int(utranValList[cellIndex]) - utranIncreament)
            
    map = {node_type + ',' + mim_version : {'EUtranCellRelation' : eutranValList,
                                            'UtranCellRelation' : utranValList,
                                            'Cdma20001xRttCellRelation' : [ '0','0','0','0'],
                                            'GeranCellRelation' : [ '1', '3', '6', '12'],
                                            'UtranFreqRelation' : ['1', '1', '1', '1']}}
    return map
    

def writeMoCfg(map):
    with open(mo_file, 'w') as f:
        for line in moInstancesInMoCfg:
            f.write(line + '\n')
        f.write(node_type + ',' + mim_version + ',')
        f.write('EUtranCellRelation,' + ','.join(map[node_type + ',' + mim_version]['EUtranCellRelation']) + ',\n')
        f.write(',,UtranCellRelation,' + ','.join(map[node_type + ',' + mim_version]['UtranCellRelation']) + ',\n')
        f.write(',,Cdma20001xRttCellRelation,' + ','.join(map[node_type + ',' + mim_version]['Cdma20001xRttCellRelation']) + ',\n')
        f.write(',,GeranCellRelation,' + ','.join(map[node_type + ',' + mim_version]['GeranCellRelation']) + ',\n')
        f.write(',,UtranFreqRelation,' + ','.join(map[node_type + ',' + mim_version]['UtranFreqRelation']) + ',\n')


def executeShellCommands():
    print 'Executing Shell Commands.'
    os.system('/netsim_users/auto_deploy/bin/TemplateGenerator.py > /dev/null')
    os.system('rm -f /pms_tmpfs/xml_step/15/* > /dev/null')
    os.system('rm -f /pms_tmpfs/LTE*/*/c/pm_data/*.xml.gz > /dev/null')
    os.system('/netsim_users/pms/bin/genStats -r 15 > /dev/null')
    print 'Shell Commands Executed.'


def findLatestFiles(map, cellid):
    path = '/pms_tmpfs/' + sim_id + '/' + map[cellid][1] + '/c/pm_data/'
    return map[cellid][1], os.path.getsize(max(glob.glob(path + '*.xml.gz'), key=os.path.getctime))


def getCellValue(index):
    if index == 0:
        return 1
    elif index == 1:
        return 3
    elif index == 2:
        return 6
    elif index == 3:
        return 12
    else:
        print 'ERROR : Invalid index ' + str(index)
        sys.exit()


def modifyMap(map, cellIndex):
    eutranValList = map[node_type + ',' + mim_version]['EUtranCellRelation']
    utranValList = map[node_type + ',' + mim_version]['UtranCellRelation']
    eutranValList[cellIndex] = eutranValList[cellIndex - 1]
    utranValList[cellIndex] = utranValList[cellIndex - 1]
    map = {node_type + ',' + mim_version : {'EUtranCellRelation' : eutranValList,
                                            'UtranCellRelation' : utranValList,
                                            'Cdma20001xRttCellRelation' : [ '0','0','0','0'],
                                            'GeranCellRelation' : [ '1', '3', '6', '12'],
                                            'UtranFreqRelation' : ['1', '1', '1', '1']}}
    return map


def startPmFileSizeFindingOperation(map):
    global utranIncreament, eutranIncreament
    moStructureInFile = {node_type + ',' + mim_version : {'EUtranCellRelation' : [ '1','1','1','1'],
                                                          'UtranCellRelation' : [ '1','1','1','1'],
                                                          'Cdma20001xRttCellRelation' : [ '0','0','0','0'],
                                                          'GeranCellRelation' : [ '1', '3', '6', '12'],
                                                          'UtranFreqRelation' : ['1', '1', '1', '1']}}
    index = 0
    operation = 'increase'
    instanceSet = False
    upDown = False
    moStructureInFileCopy = moStructureInFile
    
    while True:
        
        if index == 4:
            print 'INFO : Operation completed. Below is the final MO value'
            print moStructureInFileCopy
            break
        elif index != 0 and instanceSet:
            eutranIncreament = 40
            utranIncreament = 10
            moStructureInFileCopy = modifyMap(moStructureInFileCopy, index)
            instanceSet = False
            operation = 'increase'
            upDown = False
                
        cell_no = getCellValue(index)
        expectedFileSize = map[cell_no][0]
        moStructureInFileCopy = setNewInstances(moStructureInFileCopy, operation, index)
        writeMoCfg(moStructureInFileCopy)
        executeShellCommands()
        node_name, file_size = findLatestFiles(map, cell_no)
        file_size = int(file_size / 1024)
        if file_size == expectedFileSize:
            instanceSet = True
            index += 1
        else:
            if file_size < expectedFileSize:
                if upDown:
                    print 'WARNING : Can not achieve more increase/decrease in MO instance for file. Skipping to next iteration.'
                    index += 1
                    instanceSet = True
            elif file_size > expectedFileSize:
                operation = 'decrease'
                upDown = True
                utranIncreament, eutranIncreament = 1, 4
        

def makeBackup():
    if os.path.isfile(mo_file + '_bak'):
        os.system('rm -f ' + mo_file + '_bak')
    os.system('mv ' + mo_file + ' ' + mo_file + '_bak')       


def main():
    global simulation_name, sim_id, isLTE, finalNodeCellMap, mo_file
    
    simulation_name = raw_input('Please enter simulation name : ')
    node_family = raw_input('Please enter node category of simulation : ')
    
    if node_family.upper() == 'LTE':
        sim_id = simulation_name.split('-')[-1]
        isLTE = True
    
    if isLTE:
        finalNodeCellMap = findNodeCellRatio()
    
    printCellRatio()
    
    fileSizeValueMap = takeInputFromUserForFileSize()
    
    findAdditionalInformationForSimulation()
    
    mo_file = '/netsim_users/reference_files/' + findMoFile()
    
    loadOriginalMoInstancesFromMoCfg()
    
    makeBackup()
    
    startPmFileSizeFindingOperation(fileSizeValueMap)


if __name__ == '__main__':
    main()
