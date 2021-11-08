#!/bin/bash

if [ "$1" != "--docker" ]; then
  if [ -z "$6" ]; then
    echo "Usage: $0 [--docker] <instance-name> <gunicorn-port> <host-name> <site-name> <db-host> <db-port>"
    exit 1
  fi
  DOCKER=0
  ELAB_NAME=$1
  GUNICORN_PORT=$2
  HOST_NAME=$3
  SITE_NAME="$4"
  DB_HOST="$5"
  DB_PORT="$6"
  GUNICORN_IP=127.0.0.1
else
  DOCKER=1
  ELAB_NAME=elab
  GUNICORN_PORT=9001
  HOST_NAME=*
  SITE_NAME=elab
  DB_HOST=db
  DB_PORT=
  GUNICORN_IP=web
fi

OUTPUT_DIR=output/setup-${ELAB_NAME}

if [ -d ${OUTPUT_DIR} ]; then
  echo "Output script directory ${OUTPUT_DIR} already exists"
  exit 1
fi

mkdir -p ${OUTPUT_DIR}

# record entire command used to create this instance setup
echo -n \"$0\" > ${OUTPUT_DIR}/command
for i in "$@"; do
    echo -n \ \"$i\" >> ${OUTPUT_DIR}/command
done
echo >> ${OUTPUT_DIR}/command

if [ $DOCKER = 0 ]; then
    FILES='
    __ELAB_NAME__.conf.nginx-location
    __ELAB_NAME__.conf.supervisor
    backup.sh
    install.sh
    install-db.sh
    install-user.sh
    install-elab.sh
    check-graders.sh
    list-graders.sh
    gunicorn-start-elab.sh
    __ELAB_NAME__.crontab
    settings_local.py
    default.nginx-sites
    start-grader.sh
    tqfauthen.py
    pyplot.py
    '
else
    FILES='
    install-user.sh
    install-elab.sh
    gunicorn-start-elab.sh
    tqfauthen.py
    pyplot.py
    '
fi

for f in $FILES; do
  newfile=`echo $f | sed "s/__ELAB_NAME__/${ELAB_NAME}/"`
  cat stub/$f \
  | sed "s/__ELAB_NAME__/${ELAB_NAME}/g" \
  | sed "s/__GUNICORN_IP__/${GUNICORN_IP}/g"  \
  | sed "s/__GUNICORN_PORT__/${GUNICORN_PORT}/g"  \
  | sed "s/__HOST_NAME__/${HOST_NAME}/g"  \
  | sed "s/__SITE_NAME__/${SITE_NAME}/g"  \
  | sed "s/__DB_HOST__/${DB_HOST}/g"  \
  | sed "s/__DB_PORT__/${DB_PORT}/g"  \
  > ${OUTPUT_DIR}/$newfile
done

chmod a+x ${OUTPUT_DIR}/install-user.sh
chmod a+x ${OUTPUT_DIR}/install-elab.sh
if [ $DOCKER = 0 ]; then
  chmod a+x ${OUTPUT_DIR}/install-db.sh
  chmod a+x ${OUTPUT_DIR}/install.sh
fi

echo "Installation script generated."
echo "Examine the files inside '${OUTPUT_DIR}' folder"
echo "then execute 'install.sh' as root to begin installation"
