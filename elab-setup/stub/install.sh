#!/bin/bash

if [ $UID != 0 ]; then
    echo 'This script must be run as root.'
    exit 1
fi

./install-user.sh
./install-db.sh
./install-elab.sh

echo "*** Installing crontab ***"
su -c "crontab __ELAB_NAME__.crontab" __ELAB_NAME__

echo "*** Please perform the following operations as root ***"
echo "- Copy __ELAB_NAME__.conf.nginx-location into /etc/nginx/locations/__ELAB_NAME__.conf"
echo "- Copy __ELAB_NAME__.conf.supervisor into /etc/supervisor/conf.d/__ELAB_NAME__.conf"
echo "- Add a corresponding entry in /etc/nginx/sites-enable/default"
echo "- Restart nginx and supervisor"

