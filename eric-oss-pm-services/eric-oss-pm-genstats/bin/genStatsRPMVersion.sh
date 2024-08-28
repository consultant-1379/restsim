#!/bin/bash

################################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.13
# Purpose       :  Script is used to display GenStats RPM version which is installed in NETSim box.
# Jira No       :  NA
# Gerrit Link   :  NA
# Description   :  Script is used to display GenStats RPM version
# Date          :  31/07/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################

rpm_version=`rpm -q ERICnetsimpmcpp_CXP9029065`

if [ ! -z ${rpm_version} ];then
    echo "GenStats RPM Version: "${rpm_version}
else
    echo "GenStats is not installed properly.Please install latest GenStats version."
fi

