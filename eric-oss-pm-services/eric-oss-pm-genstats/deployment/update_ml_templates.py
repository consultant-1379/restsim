#!/usr/bin/python

import os, sys
from shutil import rmtree, copy
from time import time, localtime, strftime, gmtime
from datetime import datetime
from utilityFunctions import Utility

# Creating Objects
util = Utility()

source_template_location = '/netsim_users/pms/minilink_templates/'
sample_template_location = '/pms_tmpfs/xml_step/minilink_templates/'
precook_template_folder = '/pms_tmpfs/xml_step/minilink_templates/precook_templates/'
retain_precook_folder_count = 2
precook_folder_name, end_time = None, None
outdoor_sample_file_map = {'HEADER' : 'MiniLink_Outdoor_Header.xml', 'FOOTER' : 'MiniLink_Outdoor_Footer.xml', \
                   'A_SAMPLE' : 'MiniLink_Outdoor_A_Sample_File.xml', 'C_SAMPLE' : 'MiniLink_Outdoor_C_Sample_File.xml', \
                   'ML6352_NEW_A_SAMPLE' : 'Ml6352_New_Request_MiniLink_Outdoor_A_Sample_File.xml', \
                   'ML6352_NEW_C_SAMPLE' : 'Ml6352_New_Request_MiniLink_Outdoor_C_Sample_File.xml'}
outdoor_hard_coded_end_time = '2016-11-07T09:45:00+01:00'
fifteen_min_in_sec = 900
one_day_sec = 86400
first_execution = False

''' generate epoch second for current time '''
trigger_epoch = int(time())

def generate_end_date_time():
    global end_time
    end_time = (trigger_epoch / fifteen_min_in_sec) * fifteen_min_in_sec
    ''' request_time is the time at which requests comes from netsim '''
    global request_time
    request_time = end_time + fifteen_min_in_sec
    if os.path.isdir(precook_template_folder):
        rmtree(precook_template_folder)
    if first_execution:
        end_time += fifteen_min_in_sec
    else:
        end_time += (2 * fifteen_min_in_sec)


def createRopFolder():
    if not os.path.isdir(precook_template_folder):
        os.makedirs(precook_template_folder, 0755)
    folders = filter(None, os.listdir(precook_template_folder))
    folders.sort()
    folders.reverse()
    if len(folders) > retain_precook_folder_count:
        for f in folders[retain_precook_folder_count:]:
            rmtree(precook_template_folder + f)
            print 'Deleted ' + precook_template_folder + f + ' folder'
    global precook_folder_name
    precook_folder_name = util.getTimeInIsoFormat(end_time)
    if not os.path.isdir(precook_template_folder + precook_folder_name + '_OUTDOOR'):
        os.makedirs(precook_template_folder + precook_folder_name + '_OUTDOOR', 0755)
        return True
    return False


def generateOutdoorFooterFile(time, file_type):
    input_footer_file = sample_template_location + outdoor_sample_file_map['FOOTER']
    output_footer_file = precook_template_folder + precook_folder_name + '_OUTDOOR/' + file_type + '_FOOTER'
    with open(input_footer_file, 'r') as fin:
        with open(output_footer_file, 'w') as fout:
            for line in fin:
                line = line.rstrip()
                if 'endTime=' in line:
                    line = line.replace(outdoor_hard_coded_end_time, time)
                fout.write(line + '\n')
            fout.flush()


def generateOutdoorHeaderFile(beginTime, file_type):
    input_header = sample_template_location + outdoor_sample_file_map['HEADER']
    output_header = precook_template_folder + precook_folder_name + '_OUTDOOR/' + file_type + '_HEADER'
    with open(input_header, 'r') as h_fin:
        with open(output_header, 'w') as h_fout:
            for line in h_fin:
                line = line.rstrip()
                if 'beginTime=' in line:
                    line = line.replace('2016-10-07T02:30:00+02:00', beginTime)
                h_fout.write(line + '\n')
            h_fout.flush()


def generateOutdoorASampleFile():
    input_a_file = sample_template_location + outdoor_sample_file_map['A_SAMPLE']
    output_a_file = precook_template_folder + precook_folder_name + '_OUTDOOR/A_SAMPLE'
    offset, extra_seconds = util.generateOffSetValue(time())
    localMidnight = util.localMidnight(offset, extra_seconds, request_time - one_day_sec, one_day_sec)
    headertime = localMidnight
    headerIso = util.getTimeInIsoFormat(headertime, type=True)
    generateOutdoorHeaderFile(headerIso, 'A')
    footertime = localMidnight + (2 * one_day_sec)
    footerIso = util.getTimeInIsoFormat(footertime, type=True)
    generateOutdoorFooterFile(footerIso, 'A')
    file_data = []
    with open(input_a_file, 'r') as a_fin:
        for line in reversed(a_fin.readlines()):
            line = line.rstrip()
            if 'endTime=' in line:
                line = line.replace(outdoor_hard_coded_end_time, footerIso)
                footertime -= one_day_sec
                footerIso = util.getTimeInIsoFormat(footertime, type=True)
            file_data.append(line)
    with open(output_a_file, 'w') as a_fout:
        for line in reversed(file_data):
            a_fout.write(line + '\n')
        a_fout.flush()
    del file_data[:]


def generateOutdoorCSampleFile():
    input_c_file = sample_template_location + outdoor_sample_file_map['C_SAMPLE']
    output_c_file = precook_template_folder + precook_folder_name + '_OUTDOOR/C_SAMPLE'
    generateOutdoorFooterFile(precook_folder_name, 'C')
    temp_epoch, temp_time_string = end_time, precook_folder_name
    file_data = []
    with open(input_c_file, 'r') as c_fin:
        for line in reversed(c_fin.readlines()):
            line = line.rstrip()
            if 'endTime=' in line:
                line = line.replace(outdoor_hard_coded_end_time, temp_time_string)
                temp_epoch -= fifteen_min_in_sec
                temp_time_string = util.getTimeInIsoFormat(temp_epoch)
            file_data.append(line)
    with open(output_c_file, 'w') as c_fout:
        for line in reversed(file_data):
            c_fout.write(line + '\n')
        c_fout.flush()
    del file_data[:]
    generateOutdoorHeaderFile(temp_time_string, 'C')


def parseAndCreateNewFiles():
    generateOutdoorASampleFile()
    generateOutdoorCSampleFile()

def checkAndCopySampleFiles():
    if not os.path.isdir(sample_template_location):
        os.makedirs(sample_template_location, 0755)
        file_list_to_be_copied = [ x for x in outdoor_sample_file_map.values() if not os.path.isfile(sample_template_location + x) ]
        copySampleFiles(source_template_location, sample_template_location, file_list_to_be_copied)

def copySampleFiles(source_location, dest_location, file_list):
    for x in file_list:
        source_file = source_location + x
        if os.path.isfile(source_file):
            copy(source_file, dest_location)
        else:
            print "ERROR : " + source_file + " file not found !!"
            exit(1)

def main(args):
    if len(args) > 1:
        global first_execution
        if args[1].lower() == 'firstexecution':
            first_execution = True
    generate_end_date_time()
    checkAndCopySampleFiles()
    if createRopFolder():
        parseAndCreateNewFiles()


if __name__ == '__main__':
    main(sys.argv)

