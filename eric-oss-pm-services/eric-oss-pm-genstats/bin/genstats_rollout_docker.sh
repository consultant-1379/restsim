#!/usr/bin/sh

#Script is used to rollout Genstats on docker environment

nssDrop=$(echo ${1} | awk -F":" '{print $1}')
nssVersion=$(echo ${1} | awk -F":" '{print $2}')
nssDropAsAnInteger=$(echo ${nssDrop} | sed 's/.//g')
deploymentType=NSS

#Usage
usage()
{
    echo "usage : $(pwd)/genstats_rollout_docker.sh <nss_drop>:<nss_product_set_version>"
}

#Parse product set to get Genstats artifacts URLs
get_product_set_urls()
{
    curl --request GET "https://ci-portal.seli.wh.rnd.internal.ericsson.com/getProductSetVersionContents/?drop=${nssDrop}&productSet=NSS&version=${nssVersion}&pretty=true" > NSSProductSetContent.json

    #get jq binary. we will use this to parse the json files.
    curl -O "https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/content/repositories/nss-releases/com/ericsson/nss/scripts/jq/1.0.1/jq-1.0.1.tar"
    tar -xvf jq-1.0.1.tar
    chmod +x ./jq

    #get the version of the Genstats Product
    export MEDIAARTFACTNAME=Genstats_CXP9033278
    echo "MEDIAARTFACTNAME is ${MEDIAARTFACTNAME}"
    echo "------------------------------------------------------------------------------"
    mediaArtifactVersion=$(./jq -r --arg MEDIAARTFACTNAME1 "$MEDIAARTFACTNAME" '.[].contents[] | select(.artifactName == $MEDIAARTFACTNAME1) | .version' NSSProductSetContent.json)

    if [[ ${nssDropAsAnInteger} == 2104 ]] && [[ ${deploymentType} == "NSS" ]];then
        mediaArtifactVersion='21.04.8'
    fi
    #print the contents of the Genstats Product ISO
    echo "version of Genstats_CXP9033278 is ${mediaArtifactVersion}"
    echo "------------------------------------------------------------------------------"

    #get the content of the Genstats Product iso
    wget -q -O - --no-check-certificate --post-data="{\"isoName\":\"Genstats_CXP9033278\",\"isoVersion\":\"$mediaArtifactVersion\",\"pretty\":true,\"showTestware\":false}" https://ci-portal.seli.wh.rnd.internal.ericsson.com/getPackagesInISO/ > genstatsProductIsoContent.json

    #store the Nexus urls for the artifacts in a file
    ./jq -r '.PackagesInISO | map(.url)' genstatsProductIsoContent.json > Genstats_CXP9033278.${mediaArtifactVersion}.content


    #delete 1st and last lines of the json
    sed -i '1d' Genstats_CXP9033278.${mediaArtifactVersion}.content
    sed -i '$d' Genstats_CXP9033278.${mediaArtifactVersion}.content

    #remove double inverted colon, whitespaces, comma and update  nexus url from each line
    sed -i -e 's/^[ \t]*//;s/[ \t]*$//g' -e 's/,$//g' -e 's/"//g' -e 's/https:\/\/arm1s11-eiffel004.eiffel.gic.ericsson.se:8443\/nexus\/content\/repositories\/nss\//https:\/\/arm901-eiffel004.athtem.eei.ericsson.se:8443\/nexus\/content\/repositories\/nss-releases\//g' Genstats_CXP9033278.${mediaArtifactVersion}.content

    genstats_url=$(cat Genstats_CXP9033278.${mediaArtifactVersion}.content | grep "ERICnetsimpmcpp_CXP9029065")
    echo "Genstats RPM URL : ${genstats_url}"
    autorollout_url=$(cat Genstats_CXP9033278.${mediaArtifactVersion}.content | grep "genstatsAutoRollout")
    echo "AutoRollout ZIP URL : ${autorollout_url}"
    recording_files_url=$(cat Genstats_CXP9033278.${mediaArtifactVersion}.content | grep "recording_files")
    echo "Recoding files ZIP URL : ${recording_files_url}"
    #miniconda_url=$(cat Genstats_CXP9033278.${mediaArtifactVersion}.content| grep "Miniconda2")
    #Using hard coded url for Mininiconda
    miniconda_url="https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/content/repositories/nss-releases/com/ericsson/nss/Genstats/Miniconda2/21.07.1/Miniconda2-21.07.1.zip"
    echo "Miniconda URL : ${miniconda_url}"
}

#Download and install Genstats RPM package
install_rpm()
{
    rm -f ${genstats_url##*/}
    wget ${genstats_url}
    rm -rf /netsim_users
    rpm -Uvh --force ${genstats_url##*/}
    rm -f ${genstats_url##*/}
    cp netsim_cfg_template_omni /netsim_users/auto_deploy/bin/
    chown netsim:netsim /netsim_users/auto_deploy/bin/netsim_cfg_template_omni /netsim_users/auto_deploy/bin/netsim_cfg_gen.py
    chmod 755 /netsim_users/auto_deploy/bin/netsim_cfg_gen.py
    chown netsim:netsim -R /netsim_users /pms_tmpfs
}

#Download and unzip Recording files package
install_recordings()
{
    rm -f ${recording_files_url##*/}
    mkdir -p /netsim/genstats/
    wget ${recording_files_url}
    unzip -o ${recording_files_url##*/} -d /netsim/genstats/
    rm -f ${recording_files_url##*/}
    chown netsim:netsim -R /netsim/genstats/
}

#Download and set up auto rollout package
install_autorollout()
{
    rm -f ${autorollout_url##*/}
    wget ${autorollout_url}
    unzip -o ${autorollout_url##*/}
}

# Download and install Miniconda if not available
install_miniconda()
{
    if [ ! -d ~/miniconda ];then
        curl -L "${miniconda_url}" -o Miniconda2.sh
        bash Miniconda2.sh -b -p ~/miniconda
    fi
    if [ ! -f ~/miniconda/bin/mako-render ];then
        ~/miniconda/bin/conda install -y mako
    fi
}


# Set up Genstats 
set_up_genstats()
{
    echo netsim  | su netsim -c "touch /netsim/genstats/.dockerenv && python /netsim_users/auto_deploy/bin/getSimulationData.py --docker  && mkdir -p /netsim_users/pms/logs/ /netsim_users/pms/etc/ /netsim/genstats/logs/rollout_console && touch /netsim_users/pms/logs/GetEutranData.log /netsim_users/pms/etc/eutrancellfdd_list.txt && python /netsim_users/auto_deploy/bin/cfgGenerator.py --nssRelease ${nssDrop} --deplType NSS --edeStatsCheck False --ossEnabled False && sed -i 's/SET_BANDWIDTH_LIMITING=ON/SET_BANDWIDTH_LIMITING=OFF/g' /tmp/netsim && cp /tmp/netsim /netsim/netsim_cfg && python /netsim_users/pms/bin/GetEutranData.py && mkdir -p /netsim_users/pms/xml_templates /netsim_users/pms/rec_templates /netsim/genstats/xml_templates /netsim/genstats/logs && python /netsim_users/auto_deploy/bin/TemplateGenerator.py --docker True && /netsim_users/pms/bin/pm_setup_stats_recordings.sh -c /tmp/netsim -b False"
}

#Execute Genstats Post HC
execute_genstats_hc()
{
    script_exit_status=""
    echo "netsim" | su netsim -c "/netsim_users/hc/bin/genstat_report.sh"
    script_exit_status=$?
    if [[ ${script_exit_status} != 0 ]]; then
        echo "Exit Code : ${script_exit_status}"
        echo "Genstats Post Healthcheck Failed"
        exit 1
    fi
}


###############
# MAIN
#
if [[ -z ${nssDrop} || -z ${nssVersion} ]];then
    echo "ERROR : Provide NSS drop and NSS PSV details correctly"
    usage
    exit 2
fi


#Start Genstats rollout
echo "Genstats Rollout Started"
#Parse Product Set to get Genstats URLs
get_product_set_urls


#Install Genstats
install_miniconda
install_autorollout
install_rpm
install_recordings


#Set up Genstats
set_up_genstats
echo "Genstats Rollout Completed"


#Execute GenStats HC
echo "Initiating Genstats Post Health Check"
execute_genstats_hc
echo "Genstats Post Health Check completed"
