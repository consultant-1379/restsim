#!/bin/bash

# handling inputs
while getopts  "r:l:c:" flag
do
    case "$flag" in
        l) NE_TYPE="$OPTARG";;
        r) ROP_PERIOD_MIN="$OPTARG";;
        c) CHECK="$OPTARG";;
        *) printf "Usage: %s  [ -l ne type <NE> ] [ -r rop interval in mins ] [ -c check ADD or DELETE the node from Flexrop Configuration]\n" $0
           exit 1;;
    esac
done

# getting deployment type
DEPL_TYPE=$(cat /netsim/netsim_cfg | grep -v '#' | grep 'TYPE=' | awk -F'"' '{print $2}')

# supported node types per deployment type
if [[ "${DEPL_TYPE}" = "NSS" ]]; then
   GENSTATS_LOCAL="SPITFIRE MGW SGSN RNC vMSC-HC vMSC MSC-BC-BSP MSC-BC-IS HLR-FE-IS HLR-FE-BSP CCPC CCRC CCSM CCDM CCES SC SMSF MRS R6274 R6675 R6672 R6673 R6371 R6471-1 R6471-2 R6273 PCC PCG"
   GENSTATS_UTC="MTAS CSCF SBG VSBG VBGF MRF WCG DSC HSS-FE IPWORKS UPG BSC VSAPC"
   PLAYBACK_LOCAL="EPG-OI vEPG-OI"
else
   GENSTATS_LOCAL="R6675 R6672 SPITFIRE"
   GENSTATS_UTC="MTAS CSCF SBG VSBG VBGF MRF WCG DSC"
   PLAYBACK_LOCAL="EPG-OI vEPG-OI FrontHaul-6020 FrontHaul-6080"
fi

# creating flex rop string
flex_rop_string=""

echo ${GENSTATS_LOCAL} | grep -i ${NE_TYPE} > /dev/null
if [[ $? -eq 0  ]];then
   flex_rop_string="FLEXROP_${ROP_PERIOD_MIN}_GENSTATS_LOCAL="'"'${NE_TYPE}'"'""
else
    echo ${GENSTATS_UTC} | grep -i ${NE_TYPE} > /dev/null
    if [[ $? -eq 0  ]];then
       flex_rop_string="FLEXROP_${ROP_PERIOD_MIN}_GENSTATS_UTC="'"'${NE_TYPE}'"'""
    else
        echo ${PLAYBACK_LOCAL} | grep -i ${NE_TYPE} > /dev/null
        if [[ $? -eq 0  ]];then
           flex_rop_string="FLEXROP_${ROP_PERIOD_MIN}_PLAYBACK_LOCAL="'"'${NE_TYPE}'"'""
        else
            echo "WARNING  ${NE_TYPE}  node type is not supported by Flexible rop. Exiting..."
            exit 1
        fi
    fi
fi

#adding the create string to a file in an orderd fashion
upadte_file() {
    generation_method_rop_name="$(cut -d'=' -f1 <<<"$flex_rop_string")"
    if grep -q ${generation_method_rop_name} ${FLEX_ROP_CFG}; then
        #echo "generation_method_rop_name exists in cfg " ${generation_method_rop_name}
        # checking if proposed flex rop and node type already present in file
        current_ne_list_string=$(grep ${generation_method_rop_name} ${FLEX_ROP_CFG})
        # appending new node type to an existing string
        edited_ne_list_string=${current_ne_list_string::-1}
        #echo "edited ne list ${edited_ne_list_string}"
        updated_ne_list_string="${edited_ne_list_string} ${NE_TYPE}"'"'
        #echo "updated_ne_list_string = " ${updated_ne_list_string}
        #replace in file
        sed -i "s/$current_ne_list_string/$updated_ne_list_string/g" "$FLEX_ROP_CFG"
    else
        # append new string in a correct order
        while read -r line; do
            number_extraction_from_string=$(echo $line | cut -d'=' -f1 | tr -dc '0-9')
            # if line in file has grater or equal to current ROP the add entry above line and flag change
            if [[ ${number_extraction_from_string} -ge ${ROP_PERIOD_MIN} ]]; then
                sed -i "/$line/i $flex_rop_string" "$FLEX_ROP_CFG"
                # exit after update
                exit 1
            fi
        done < ${FLEX_ROP_CFG}
        echo "$flex_rop_string" >> "$FLEX_ROP_CFG"
    fi
}


# checking cfg existance and running file update
FLEX_ROP_CFG="/netsim_users/pms/etc/flex_rop_cfg"
if [ "$CHECK" = "ADD" ];then
   if [ -r ${FLEX_ROP_CFG} ] ; then
      upadte_file
   else
      echo '#!/bin/bash' > ${FLEX_ROP_CFG}
      echo ${flex_rop_string} >>  ${FLEX_ROP_CFG}
      echo "INFO created ${FLEX_ROP_CFG} file"
   fi
else
   methodname="$(cut -d'=' -f1 <<<"$flex_rop_string")"
   if grep -q ${methodname} ${FLEX_ROP_CFG}; then
       ne_list_string=$(grep ${methodname} ${FLEX_ROP_CFG})
       nodelist=$(echo ${ne_list_string} | awk -F'"' '{print $2}')
       mod=${nodelist/" "${NE_TYPE}/''}
       mod=${mod/${NE_TYPE}" "/''}
       if [ ${mod} == ${NE_TYPE} ];then
          sed -i "/$methodname/d" "$FLEX_ROP_CFG"
       else
          new_list_string="$methodname"'="'"$mod"'"'
          sed -i "s/$ne_list_string/$new_list_string/g" "$FLEX_ROP_CFG"
       fi
   fi
fi
