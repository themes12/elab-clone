#!/bin/bash

BOX_USER=elabdummy
BOX_GROUP=elabdummy

if [ $UID != 0 ]; then
    echo 'This script must be run as root.'
    exit 1
fi

echo 'Create box user if necessary...'
id ${BOX_USER} || adduser --disable-password --gecos "" ${BOX_USER}

echo 'Installing box in sandbox/box...'
(cd sandbox; g++ -m32 -o box box.cc)
chown ${BOX_USER}:${BOX_GROUP} sandbox/box
chmod u+s sandbox/box

echo '*** NOTES ***'
echo 'In order to support certain task types,'
echo 'You may need to add box user "elabdummy"'
echo 'to the same group of the user running elab.'
