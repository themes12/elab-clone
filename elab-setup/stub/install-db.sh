#!/bin/bash

HOME_DIR=/home/__ELAB_NAME__
ELAB_DIR=${HOME_DIR}/app/elabsheet

echo "*** Creating database for __ELAB_NAME__ ***"
read -p "Enter elab database password: " elabpass
echo "Enter MySQL root password"

# Use this line instead if mysql's root account requires a password
#mysql -u root -p << EOF

mysql << EOF
CREATE DATABASE __ELAB_NAME__
  DEFAULT CHARACTER SET utf8
  DEFAULT COLLATE utf8_general_ci;
CREATE USER '__ELAB_NAME__'@'localhost' IDENTIFIED BY '$elabpass';
GRANT ALL PRIVILEGES ON __ELAB_NAME__.* TO '__ELAB_NAME__'@'localhost';
EOF

mv settings_local.py settings_local.tmp
sed "s/__DB_PASSWD__/$elabpass/g" settings_local.tmp > settings_local.py
rm settings_local.tmp
