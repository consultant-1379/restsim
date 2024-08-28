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
# Version no    :  NSS 18.07
# Purpose       :  
# Jira No       :  
# Gerrit Link   :  
# Description   :  
# Date          :  21/03/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

import os
import sys
from _collections import defaultdict

input_mim = None
output_cfg = None
instance = 1
relationMap = defaultdict(list)
classDataList = []

def writeCfgFile():
    with open(output_cfg,'w') as cfg:
        for key, vals in relationMap.items():
            uniq_list = set(vals)
            for val in uniq_list:
                if val in classDataList:
                    cfg.write(val + ',' + str(instance) + ',' + key + '\n')


def parseMimFile():
    import xml.etree.cElementTree as ET

    tree = ET.ElementTree(file=input_mim)
    root = tree.getroot()
    
    global classDataList, relationMap
    
    classId = ''
    attrName = ''
    
    for className in root.getiterator('class'):
        classId = className.get('name')
        for attr in className.getiterator('attribute'):
            attrName = attr.get('name')
            if attrName.startswith('pm'):
                classDataList.append(classId)
                classId = attrName = ''
                break
    
    parentMo = ''
    childMo = ''

    for relation in root.getiterator('relationship'):
        for parent in relation.getiterator('parent'):
            for hasClass in parent.getiterator('hasClass'):
                parentMo = hasClass.get('name')
        for child in relation.getiterator('child'):
            for hasClass in child.getiterator('hasClass'):
                childMo = hasClass.get('name')
        if parentMo and childMo:
            relationMap[parentMo].append(childMo)
            parentMo = childMo = ''


def exit_code(message):
    print ('ERROR: ' + message)
    print ('INFO: Exiting process.')
    sys.exit(1)


def main(argv):
    global input_mim, output_cfg
    
    if not len(argv) == 2:
        exit_code('Invalid number of argument provided.')
    
    input_mim = argv[0]
    output_cfg = argv[1]
    
    if not input_mim or not output_cfg:
        exit_code('Argument value should not be empty or white space only.')
        
    if not os.path.isfile(input_mim):
        exit_code(input_mim + ' file not present.')
    
    if not os.path.isdir(os.path.dirname(output_cfg)):
        exit_code('Directory ' + os.path.dirname(output_cfg) + ' not present.')
    
    parseMimFile()
    writeCfgFile()


if __name__ == '__main__':
    main(sys.argv[1:])

