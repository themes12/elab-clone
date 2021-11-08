#!/bin/bash

echo "*** Creating user __ELAB_NAME__ ***"
adduser --disabled-password --gecos "" __ELAB_NAME__
adduser elabdummy __ELAB_NAME__

echo "*** Preparing home directory ***"
HOME_DIR=/home/__ELAB_NAME__
ELAB_DIR=${HOME_DIR}/app/elabsheet

su -c "
    cd ${HOME_DIR}
    mkdir -p app backup logs
" __ELAB_NAME__

echo "*** Preparing virtual environment ***"
su -c "
    cd ${HOME_DIR}
    mkdir virtualenv
    cd virtualenv
    python3.6 -m venv __ELAB_NAME__
    . __ELAB_NAME__/bin/activate
    pip install --no-cache-dir numpy matplotlib
" __ELAB_NAME__
