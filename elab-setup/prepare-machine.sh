#!/bin/bash

if [ $UID != 0 ]; then
    echo 'This script must be run as root.'
    exit 1
fi

apt-get update
dpkg --add-architecture i386

apt-get install -y apt-utils cron
apt-get install -y mysql-client libmysqlclient-dev
apt-get install -y python-minimal python-dev python-virtualenv
apt-get install -y build-essential g++-multilib mercurial git-core
apt-get install -y openjdk-9-jdk-headless 
apt-get install -y mono-mcs
apt-get install -y gunicorn supervisor
apt-get install -y \
    libsasl2-dev python-dev libldap2-dev openssl libssl-dev \
    libsqlite3-dev libbz2-dev libreadline-dev libncurses5-dev \
    libgdbm-dev liblzma-dev

ln -s /usr/bin/mcs /usr/bin/gmcs

locale-gen en_US.UTF-8

adduser --disabled-password --gecos "" elabdummy

update-rc.d supervisor defaults

if [ "$1" != "--docker" ]; then
    # install mysql-server and nginx
    apt-get install -y mysql-server
    apt-get install -y nginx

    # download and install Python 3.6.5
    mkdir src
    cd src
    wget https://www.python.org/ftp/python/3.6.5/Python-3.6.5.tar.xz
    tar xf Python-3.6.5.tar.xz
    cd Python-3.6.5
    ./configure --prefix=/opt/python-3.6.5
    make
    make install

    # install MathJax 2
    cd /opt
    wget https://github.com/mathjax/MathJax/archive/2.7.9.tar.gz
    tar xf 2.7.9.tar.gz
    rm 2.7.9.tar.gz
    cd /var/www/html
    ln -s /opt/MathJax-2.7.9 mathjax
fi

ln -sf /opt/python-3.6.5/bin/python3.6 /usr/local/bin/python3.6

# install numpy and matplotlib
/opt/python-3.6.5/bin/pip3 install numpy matplotlib
