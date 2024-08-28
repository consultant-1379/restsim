#!/bin/bash

echo "###=== New Entry ===###"
echo "`date` Started logging"
if [[ -d /var/log/ ]]; then
    for log_file in `ls /var/log/`; do
        tail -n+1 -F /var/log/${log_file} &
    done
else
    echo "Log dir not ready yet"
fi
echo "`date` Finished logging"

while true; do
    sleep 900
done
