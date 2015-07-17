* 1 * * * bash -l -c 'python /adsws/manage.py accounts cleanup_tokens' >> /tmp/cron.log 2>&1
* 2 * * * bash -l -c 'python /adsws/manage.py accounts cleanup_clients' >> /tmp/cron.log 2>&1
* */2 * * * bash -l -c 'python /adsws/manage.py accounts cleanup_users' >> /tmp/cron.log 2>&1

