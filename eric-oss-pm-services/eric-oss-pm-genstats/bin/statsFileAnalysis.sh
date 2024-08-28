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
# Purpose       :  Script is responsible to do data analysis regarding number of counter, cell and cell relation and xml and gz file size
# Jira No       :  
# Gerrit Link   :  
# Description   :  New code
# Date          :  25/07/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

input_file_location=$1
output_file_location=$2
node_type=$3

mkdir -p "${output_file_location}"

output_data="/tmp/${node_type}_info.txt"

touch "${output_data}"
echo "File_Name;No_Cells;No_Relations;No_Counters;XML_FILESIZE;GZ_FILESIZE" >> ${output_data}

folder_list=($(ls ${input_file_location}))

for folder in ${folder_list[@]}
do
    file_list=($(ls ${input_file_location}/${folder}))

    for file_name in ${file_list[@]}
    do
        gz_filename=$(echo "${file_name}.gz")
        temp_data=$(ls -lrt ${input_file_location}/${folder}/${file_name})
        file_size=$(echo ${temp_data} | cut -d' ' -f5)

        cp "${input_file_location}/${folder}/${file_name}" "${output_file_location}/"

        no_of_counters=""
        no_of_uniq_cells=""
        no_of_uniq_relations=""

        if [[ "${node_type}" = "CPP" ]]; then
            no_of_counters=$(cat "${output_file_location}/${file_name}" | grep '<r>' | wc -l )
            no_of_uniq_cells=$(cat "${output_file_location}/${file_name}" | grep '<moid>' | perl -ne 'chomp;print scalar reverse . "\n";' | cut -d',' -f1 | perl -ne 'chomp;print scalar reverse . "\n";' | grep EUtranCellFDD | sort -u | wc -l )
            no_of_uniq_relations=$(cat "${output_file_location}/${file_name}" | grep '<moid>' | perl -ne 'chomp;print scalar reverse . "\n";' | cut -d',' -f1 | perl -ne 'chomp;print scalar reverse . "\n";' | grep CellRelation | sort -u | wc -l )
        elif [[ "${node_type}" = "ECIM" ]]; then
            no_of_counters=$(cat "${output_file_location}/${file_name}" | grep '<r p=' | wc -l )
            no_of_uniq_cells=$(cat "${output_file_location}/${file_name}" | grep '<measValue ' | perl -ne 'chomp;print scalar reverse . "\n";' | cut -d',' -f1 | perl -ne 'chomp;print scalar reverse . "\n";' | grep EUtranCellFDD | sort -u | wc -l )
            no_of_uniq_relations=$(cat "${output_file_location}/${file_name}" | grep '<measValue ' | perl -ne 'chomp;print scalar reverse . "\n";' | cut -d',' -f1 | perl -ne 'chomp;print scalar reverse . "\n";' | grep CellRelation | sort -u | wc -l )
        fi

        gzip "${output_file_location}/${file_name}"

        temp_data_gz=$(ls -lrt ${output_file_location}/${file_name}.gz)
        file_size_gz=$(echo ${temp_data_gz} | cut -d' ' -f5)

        echo "${file_name};${no_of_uniq_cells};${no_of_uniq_relations};${no_of_counters};${file_size};${file_size_gz}" >> ${output_data}

        rm -f "${output_file_location}/${file_name}.gz"

    done
done

echo "Operation completed successfully."

