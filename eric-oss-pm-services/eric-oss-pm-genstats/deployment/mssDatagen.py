#!/usr/bin/python

from _collections import defaultdict
from calendar import timegm
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
import os, sys, getopt, gzip, ConfigParser
from subprocess import Popen, PIPE
from time import gmtime, localtime, strftime, mktime


info, warn, error, instr = '[INFO] : ', '[WARNING] : ', '[ERROR] : ', '[INSTRUMENTATION] : '
EPOCH_DATETIME = datetime(1970, 1, 1)
SECONDS_PER_DAY = 86400
CONFIG_FILE = '/netsim_users/reference_files/config.ini'
FILE_TIMESTAMP_FORMAT , FILE_TIMESTAMP_FORMAT_TILL_MIN = '%y%m%d%H%M%S', '%y%m%d%H%M00'
FILE_TIMESTAMP_FORMAT_ONLY_TIME, FILE_TIMESTAMP_FORMAT_TILL_DATE = '%H%M%S', '%y%m%d'
DATA_CONVERSION , DATA_PLAYBACK = False, False
serverStartTime = serverEndTime = serverStartOffset = serverEndOffset = deltaTime = None
oldFileStartTime = oldFileEndTime = utcStartDateTime = utcEndDateTime = None
symlinkDirs = {}
nodeFileListMap = defaultdict(list)
offsetVariation = False
multiProcessInstance = 1
sourceDataLocation = destDataLocation = None
eventParamMap = {0 : ['"seizureTime"', '"answerTime"', '"releaseTime"', '"startTime"'],
                 1 : ['"seizureTime"', '"answerTime"', '"releaseTime"', '"startTime"'],
                 2 : ['"seizureTime"', '"answerTime"', '"releaseTime"', '"startTime"'],
                 3 : ['"seizureTime"', '"answerTime"', '"releaseTime"', '"startTime"'],
                 4 : ['"originationTime"'], 5 : ['"deliveryTime"'], 6 : ['"eventTime"']}
EVENT_COLLECT_TAG = '<eventCollec '
EVENT_ID_TAG = '<event id='
EVENT_PARAM_TAG = '<ie name='
END_EVENT_TAG = '</event>'

def run_shell_command(input_cmd):
    output = Popen(input_cmd, stdout=PIPE, shell=True).communicate()[0]
    return output


def getCurrentDateTime():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' '


def throw_message(_str, _status):
    print getCurrentDateTime() + _status + _str


def fileCollector(location):
    global nodeFileListMap
    
    listOfFile = filter(None, os.listdir(location))
    
    if DATA_PLAYBACK:
        for file in listOfFile:
            initTime = datetime.strptime(file.split('-')[0].split('.')[-1][-6:], FILE_TIMESTAMP_FORMAT_ONLY_TIME)
            oneObj , twoObj = datetime.strptime(utcStartDateTime[-6:], FILE_TIMESTAMP_FORMAT_ONLY_TIME), datetime.strptime(utcEndDateTime.strftime(FILE_TIMESTAMP_FORMAT_ONLY_TIME), FILE_TIMESTAMP_FORMAT_ONLY_TIME)
            if initTime >= oneObj and initTime < twoObj:
                nodeFileListMap[file.split('.')[0]].append(file)
    elif DATA_CONVERSION:
        for file in listOfFile:
            nodeFileListMap[file.split('.')[0]].append(file)


def validating_information():
    requiredParamFromConfig()
    
    if not os.path.isdir(sourceDataLocation):
        throw_message(sourceDataLocation + ' directory does not exists.', error)
        return False

    if not os.path.isdir(destDataLocation):
        throw_message(destDataLocation + ' directory not present.', error)
        return False

    fileCollector(sourceDataLocation)

    if not nodeFileListMap:
        throw_message('No file found at ' + sourceDataLocation, error)
        return False
    
    if DATA_PLAYBACK:
        global deltaTime, oldFileStartTime, oldFileEndTime
        for node_name, file_names in nodeFileListMap.iteritems():
            fileElements = file_names[0].split('.')[2].split('_')[0].split('-')
            oldFileStartTime , oldFileEndTime = fileElements[0], fileElements[1]
            deltaTime = (datetime.strptime(utcStartDateTime[:6], FILE_TIMESTAMP_FORMAT_TILL_DATE) - datetime.strptime(oldFileStartTime[:6], FILE_TIMESTAMP_FORMAT_TILL_DATE)).days * SECONDS_PER_DAY
            return True
    else:
        return True
    

def findTotalSeconds(_datetimeObj):
    return (SECONDS_PER_DAY * _datetimeObj.days) + _datetimeObj.seconds


def createDirectory():
    for nodeName in nodeFileListMap.iterkeys():
        path = destDataLocation + '/' + nodeName
        if not os.path.isdir(path):
            os.mkdir(path)


def utcToLocalTimeConversion(inputUtcTime):
    timeStruct = localtime(findTotalSeconds(inputUtcTime - EPOCH_DATETIME))
    return datetime.fromtimestamp(mktime(timeStruct))


def logInstrumentation(logMap, file_name):
    _totalEvents = 0
    _str = file_name + ' : '
    for event_id in eventParamMap.keys():
        if logMap.has_key(event_id):
            eveCount = logMap.get(event_id)
            _totalEvents = _totalEvents + eveCount
            _str = _str + str(event_id) + '=' + str(eveCount) + ', '
        else:
            _str = _str + str(event_id) + '=0, '
    _str = _str[:-2] + ' : Total_Events=' + str(_totalEvents)
    throw_message(_str, instr)


def parseFileContent(content, outputFile):
    instumentLogMap = {}
    beginCheck = False
    eventId = None
    out = gzip.open(outputFile, 'w')
    for line in content:
        lineCpy = line.strip()
        if beginCheck:
            if lineCpy.startswith(EVENT_ID_TAG):
                eventId = int(lineCpy.split('"')[1])
                if instumentLogMap.has_key(eventId):
                    instumentLogMap[eventId] = instumentLogMap.get(eventId) + 1
                else:
                    instumentLogMap[eventId] = 1
            elif lineCpy == END_EVENT_TAG:
                eventId = None
            elif eventId != None and lineCpy.startswith(EVENT_PARAM_TAG) and eventParamMap.has_key(eventId):
                if any(param in lineCpy for param in eventParamMap.get(eventId)):
                    oldParamUtcDateTime = lineCpy.split('>')[1].split('<')[0]
                    newParamUtcDateTime = datetime.strptime(oldParamUtcDateTime, FILE_TIMESTAMP_FORMAT) + timedelta(seconds=deltaTime)
                    newParamLocalDateTime = utcToLocalTimeConversion(newParamUtcDateTime)
                    newParamLocalDateTimeStr = newParamLocalDateTime.strftime(FILE_TIMESTAMP_FORMAT)
                    if offsetVariation:
                        if newParamLocalDateTime >= serverEndTime:
                            newParamLocalDateTimeStr = newParamLocalDateTimeStr + serverEndOffset
                        else:
                            newParamLocalDateTimeStr = newParamLocalDateTimeStr + serverStartOffset
                    else:
                        newParamLocalDateTimeStr = newParamLocalDateTimeStr + serverStartOffset
                    out.write(line.replace(oldParamUtcDateTime, newParamLocalDateTimeStr))
                    continue
        else:
            if lineCpy.startswith(EVENT_COLLECT_TAG):
                beginCheck = True
                oldBeginValue = lineCpy.split('"')[1]
                newBeginLocalStr = utcToLocalTimeConversion(datetime.strptime(oldBeginValue, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=deltaTime)).strftime('%Y-%m-%dT%H:%M:%SZ')
                out.write(line.replace(oldBeginValue, newBeginLocalStr))
                continue
        out.write(line)
    out.flush()
    out.close()
    logInstrumentation(instumentLogMap, outputFile.split('/')[-1])
                    
                    
def generateOutputFile(input_file, output_file):
    _reader = gzip.open(input_file, 'r')
    parseFileContent(_reader, output_file)
    _reader.close()


def readFileAndGenerateData(node_name, fileName):
    elements = fileName.split('-')
    _initTime, _termTime = elements[0].split('.')[-1], elements[1].split('_')[0]
    _termTimeObj = datetime.strptime(_termTime, FILE_TIMESTAMP_FORMAT) + timedelta(seconds=deltaTime)
    fileInitTime = elements[0].replace(_initTime, utcToLocalTimeConversion(datetime.strptime(_initTime, FILE_TIMESTAMP_FORMAT) + timedelta(seconds=deltaTime)).strftime(FILE_TIMESTAMP_FORMAT) + serverStartOffset)
    fileTerminateTime = ''
    if offsetVariation:
        if _termTimeObj >= utcEndDateTime:
            fileTerminateTime = elements[1].replace(_termTime, utcToLocalTimeConversion(_termTimeObj).strftime(FILE_TIMESTAMP_FORMAT) + serverEndOffset)
        else:
            fileTerminateTime = elements[1].replace(_termTime, utcToLocalTimeConversion(_termTimeObj).strftime(FILE_TIMESTAMP_FORMAT) + serverStartOffset)
    else:
        fileTerminateTime = elements[1].replace(_termTime, utcToLocalTimeConversion(_termTimeObj).strftime(FILE_TIMESTAMP_FORMAT) + serverStartOffset)
    outputGzFileName = fileInitTime + '.' + fileTerminateTime
    inputGzFilePath = sourceDataLocation + '/' + fileName
    outputGzFilePath = destDataLocation + '/' + node_name + '/' + outputGzFileName
    generateOutputFile(inputGzFilePath, outputGzFilePath)
    return outputGzFilePath
    

def getRequiredTimeDetails():
    global serverStartTime, serverEndTime, serverStartOffset, serverEndOffset, utcStartDateTime, utcEndDateTime
    serverStartOffset = run_shell_command('date "+%z"').strip()
    serverEndOffset = run_shell_command('date --date="1 min" "+%z"').strip()
    serverStartTime = datetime.now().strftime(FILE_TIMESTAMP_FORMAT_TILL_MIN)
    serverEndTime = datetime.strptime(serverStartTime, FILE_TIMESTAMP_FORMAT_TILL_MIN) + timedelta(seconds=60)
    utcStartDateTime = datetime.utcnow().strftime(FILE_TIMESTAMP_FORMAT_TILL_MIN)
    utcEndDateTime = datetime.strptime(utcStartDateTime, FILE_TIMESTAMP_FORMAT_TILL_MIN) + timedelta(seconds=60)
    if serverStartOffset != serverEndOffset:
        global offsetVariation
        offsetVariation = True


def createSymbolicLinks(_list):
    if not _list:
        throw_message('No output MSS file created.', error)

    for filePath in _list:
        node = filePath.split('/')[-1].split('.')[0]
        if symlinkDirs.has_key(node):
            symPath = symlinkDirs.get(node)
            if not os.path.isdir(symPath):
                os.mkdir(symPath)
            command = 'ln -s ' + filePath + ' ' + symPath + '/' + filePath.split('/')[-1]
            run_shell_command(command)
        else:
            throw_message('Can not create symbolic link for file : ' + filename + ' as path is not defined in ' + CONFIG_FILE, error)
    

def initializeDataPlaybackMode():
    getRequiredTimeDetails()
    validationCheck = validating_information()
    outputFileList = []
    if validationCheck:
        createDirectory()
        
        pool = Pool(multiProcessInstance)
        
        for nodeName, fileLists in nodeFileListMap.iteritems():
            for fileName in fileLists:
                # pool.apply_async(readFileAndGenerateData, args=(nodeName, fileName,),callback = outputFileList.append)
                outputFileList.append(readFileAndGenerateData(nodeName, fileName))

        pool.close()
        pool.join()

    createSymbolicLinks(outputFileList)
    

def findOffsetToSecondsAndBehavior(_offsetStr):
    offsetBehavior = _offsetStr[:1]
    absOffset = datetime.strptime(_offsetStr[-4:], '%H%M')
    absOffsetToSeconds = (absOffset.hour * 3600) + (absOffset.minute * 60)
    return (absOffsetToSeconds, offsetBehavior)


def convertLocalTimeToUTC(_time):
    localTime = datetime.strptime(_time[:-5], FILE_TIMESTAMP_FORMAT)
    offset = findOffsetToSecondsAndBehavior(_time[-5:])
    if str(offset[1]) == '+':
        return (localTime - timedelta(seconds=int(offset[0]))).strftime(FILE_TIMESTAMP_FORMAT)
    else:
        return (localTime + timedelta(seconds=int(offset[0]))).strftime(FILE_TIMESTAMP_FORMAT)


def writeUtcFile(content, destFile, ropLocalTime, ropLocalStartOffset, ropLocalEndOffset):
    beginCheck = False
    eventId = None
    gzipOut = gzip.open(destFile, 'w')
    for line in content:
        lineCpy = line.strip()
        if beginCheck:
            if lineCpy.startswith(EVENT_ID_TAG):
                eventId = int(lineCpy.split('"')[1])
            elif lineCpy == END_EVENT_TAG:
                eventId = None
            elif eventId != None and lineCpy.startswith(EVENT_PARAM_TAG) and eventParamMap.has_key(eventId):
                if any(param in lineCpy for param in eventParamMap.get(eventId)):
                    oldParamLocalValue = lineCpy.split('>')[1].split('<')[0]
                    gzipOut.write(line.replace(oldParamLocalValue, convertLocalTimeToUTC(oldParamLocalValue)))
                    continue
        else:
            if lineCpy.startswith(EVENT_COLLECT_TAG):
                beginCheck = True
                oldBeginValue = lineCpy.split('"')[1]
                oldBeginDateObj = datetime.strptime(oldBeginValue, '%Y-%m-%dT%H:%M:%SZ')
                offsetToBeApplied = ropLocalStartOffset
                if ropLocalStartOffset != ropLocalEndOffset:
                    if oldBeginDateObj >= datetime.strptime(ropLocalTime.split('.')[1][-5:], FILE_TIMESTAMP_FORMAT_TILL_MIN):
                        offsetToBeApplied = ropLocalEndOffset
                newBeginValue = datetime.strptime(convertLocalTimeToUTC(oldBeginDateObj.strftime(FILE_TIMESTAMP_FORMAT) + offsetToBeApplied), FILE_TIMESTAMP_FORMAT).strftime('%Y-%m-%dT%H:%M:%SZ')
                gzipOut.write(line.replace(oldBeginValue, newBeginValue))
                continue
        gzipOut.write(line)
    gzipOut.flush()
    gzipOut.close()
        

def readSourceFile(sourceFile, destFile, localRopTime, initOffset, terminateOffset):
    _reader = gzip.open(sourceFile, 'r')
    writeUtcFile(_reader, destFile, localRopTime, initOffset, terminateOffset)
    _reader.close()
        

def startConvertingInputDataToUTC(fileName):
    timeElements = fileName.split('.')
    fileInitTimeLocal, fileTerminateTimeLocal = timeElements[2], timeElements[3].split('_')[0]
    fileInitTimeLocalOffset , fileTerminateTimeLocalOffset = fileInitTimeLocal[-5:], fileTerminateTimeLocal[-5:]
    fileRopTimeLocal = fileInitTimeLocal + '.' + fileTerminateTimeLocal
    fileInitTimeUTC, fileTerminateTimeUTC = convertLocalTimeToUTC(fileInitTimeLocal), convertLocalTimeToUTC(fileTerminateTimeLocal)
    newGzFilePath = destDataLocation + '/' + fileName.replace(fileRopTimeLocal, fileInitTimeUTC + '-' + fileTerminateTimeUTC)
    sourceGzFilePath = sourceDataLocation + '/' + fileName
    readSourceFile(sourceGzFilePath, newGzFilePath, fileRopTimeLocal, fileInitTimeLocalOffset , fileTerminateTimeLocalOffset)


def initializeDataConversionMode():
    validationCheck = validating_information()
    
    if validationCheck:
        pool = Pool(multiProcessInstance)
        
        for fileLists in nodeFileListMap.itervalues():
            for fileName in fileLists:
                # pool.apply_async(startConvertingInputDataToUTC, args=(fileName,),)
                startConvertingInputDataToUTC(fileName)
        
        pool.close()
        pool.join()

        
def helpMessages(_msg, status):
    print _msg
    sys.exit(status)


def requiredParamFromConfig():
    global sourceDataLocation, destDataLocation, multiProcessInstance, symlinkDirs
    
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    
    if DATA_PLAYBACK:
        sourceDataLocation = config.get('ATTR', 'INTERMEDIATE_DATA_LOCATION')
        destDataLocation = config.get('ATTR', 'DESTINATION_LOCATION')
    else:
        sourceDataLocation = config.get('ATTR', 'SOURCE_DATA_LOCATION')
        destDataLocation = config.get('ATTR', 'INTERMEDIATE_DATA_LOCATION')
        
    multiProcessInstance = config.getint('ATTR', 'MULTIPROCESS_INSTANCE')
    if multiProcessInstance < 1:
        multiProcessInstance = 1
        
    for path in config.get('ATTR', 'SYMLINK_LOCATION').split(','):
        name = path.split('/')[-1].strip()
        if not name:
            name = path.split('/')[-2].strip()
        symlinkDirs[name] = path

    
def main():
    global DATA_CONVERSION, DATA_PLAYBACK
    
    if not os.path.isfile(CONFIG_FILE):
        helpMessages(CONFIG_FILE + ' file not available.', 1)
    
    inputArgs = sys.argv[1:]
    
    if not inputArgs:
        helpMessages('TO KNOW SCRIPT USAGE : python mss_datagen.py -h/--help', 1)
    
    try:
        options, remainder = getopt.getopt(inputArgs, 'm:h', ['mode=', 'help'])
    except:
        helpMessages('TO KNOW SCRIPT USAGE : python mss_datagen.py -h/--help', 1)
        
    for opt, value in options:
        if opt in ('-m', '--mode'):
            value = value.upper()
            if value == 'DATAPLAYBACK':
                DATA_PLAYBACK = True
                initializeDataPlaybackMode()
            elif value == 'DATACONVERSION':
                DATA_CONVERSION = True
                initializeDataConversionMode()
            else:
                helpMessages('ERROR: Unsupported output selected.\nTO KNOW SCRIPT USAGE : python mss_datagen.py -h/--help', 1)
        elif opt in ('-h', '--help'):
            helpMessages('USAGE :  python mss_datagen.py -m DATAPLAYBACK/DATACONVERSION OR --mode=DATAPLAYBACK/DATACONVERSION', 0)
    sys.exit(0)

   
if __name__ == '__main__':
    main()

