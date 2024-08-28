#!/bin/bash

echo "Starting file metdata generation..."
nohup python /netsim_users/pms/bin/fileMetdataGenerator.py -e  >> /netsim_users/pms/logs/fileMetadata.log & 
echo "Started in background."
