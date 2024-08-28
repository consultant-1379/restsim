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

# Variables Declaration
SIM_LIST="CORE-FT-CSCF-TSP-7-2x1 CORE-FT-HSS-FE-TSP-16Ax1 CORE-FT-MTAS-TSP-4-4x1"

runTest(){
   SIM=$1
   node=`ls /pms_tmpfs/$SIM | head -1`

   if [[ ${SIM} =~ "CSCF-TSP" ]] ; then
       file=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep cscf`
	   format=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep cscf | grep -v gz`
	   echo ${file} && echo ${format}  > /dev/null
           if [ ! -z ${file} ] || [ ! -z ${format} ];then
	   if [ $? -eq 0 ] ; then
	      echo "Passed: File Format matched for CSCF-TSP"
		  return 0;
	   fi
           else
              echo "No file generation for TSP CSCF simulation."
              return 1;
           fi
   elif [[ ${SIM} =~ "HSS-FE-TSP" ]] ; then
	   file=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep HSS-AVG`
	   format=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep HSS-AVG | grep -v gz`
           echo ${file} && echo ${format}  > /dev/null
           if [ ! -z ${file} ] || [ ! -z ${format} ];then
           if [ $? -eq 0 ] ; then
              echo "Passed: File Format matched for HSS-FE-TSP"
                  return 0;
           fi
           else
              echo "No file generation for TSP HSS-FE simulation."
              return 1;
           fi 

   elif [[ ${SIM} =~ "MTAS-TSP" ]] ; then
	   file=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep MtasTraf`
	   format=`ls /pms_tmpfs/${SIM}/${node}/opt/telorb/axe/tsp/NM/PMF/reporterLogs | grep MtasTraf | grep -v gz`
           echo ${file} && echo ${format}  > /dev/null
           if [ ! -z ${file} ] || [ ! -z ${format} ];then
           if [ $? -eq 0 ] ; then
              echo "Passed: File Format matched for MTAS-TSP"
                  return 0;
           fi
           else
              echo "No file generation for MTAS-TSP simulation."
              return 1;
           fi
   else
       echo "No TSP Simulations found."
       return 1;
   fi   
}

for SIM in ${SIM_LIST};do 
    if grep -q ${SIM} "/tmp/showstartednodes.txt"; then
        runTest ${SIM}
    fi
done
