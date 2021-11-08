#!/bin/sh

secret=`head /dev/urandom | tr -dc A-Za-z0-9 | head -c64`

git submodule init
git submodule update

cp src/elabsheet/requirements.txt elab-setup/
sed "s/^SECRET_KEY.*$/SECRET_KEY = '${secret}'/" \
  config/settings_local.py > src/elabsheet/elabsheet/settings_local.py
ln -sf /home/elab/virtualenv/elab/bin/activate src/elabsheet/ve

(
  cd elab-setup
  docker build -f Dockerfile-machine -t cjaikaeo/elab-machine .
  docker build -f Dockerfile-base -t cjaikaeo/elab-base .
)
