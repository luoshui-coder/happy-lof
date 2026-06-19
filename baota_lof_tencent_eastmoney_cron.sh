#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
echo $$ > /www/server/cron/feaa277227b3073e6b9448db76cea763.pl
cd /www/scripts/ && python3 baota_lof_tencent_eastmoney_push.py
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
if [[ "$1" != "start" ]]; then
    btpython /www/server/panel/script/log_task_analyzer.py /www/server/cron/feaa277227b3073e6b9448db76cea763.log
fi
rm "/www/server/cron/feaa277227b3073e6b9448db76cea763.pl"
