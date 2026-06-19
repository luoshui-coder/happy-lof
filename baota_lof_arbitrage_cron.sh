#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
echo $$ > /www/server/cron/55782e37ba9b711fe2f46303d9ae0e24.pl
cd /www/scripts/ && python3 baota_lof_arbitrage_push.py
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
if [[ "$1" != "start" ]]; then
    btpython /www/server/panel/script/log_task_analyzer.py /www/server/cron/55782e37ba9b711fe2f46303d9ae0e24.log
fi
rm "/www/server/cron/55782e37ba9b711fe2f46303d9ae0e24.pl"
