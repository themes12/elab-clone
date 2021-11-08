#!/bin/sh

HOME_DIR=/home/elab
ELAB_DIR=${HOME_DIR}/app/elabsheet

while ! nc -z web 9001 > /dev/null; do
  echo 'Waiting for elab-web to be ready...'
  sleep 1
done

su -c "
  . ${HOME_DIR}/virtualenv/elab/bin/activate ve
  cd ${ELAB_DIR}
  ./manage.py run_grader
" elab
