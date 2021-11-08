#!/bin/sh

BACKUP_DIR=~/backup
STAMP=`date +%F`
DB_FILE=${BACKUP_DIR}/__ELAB_NAME__.db.${STAMP}.sql.gz
MEDIA_FILE=${BACKUP_DIR}/__ELAB_NAME__.media.${STAMP}.tar.gz

echo "Creating database backup ${DB_FILE}..."
mysqldump -u __ELAB_NAME__ -p __ELAB_NAME__ | gzip -c > ${DB_FILE}

echo "Creating media&supplements backup ${MEDIA_FILE}..."
tar zcf ${MEDIA_FILE} app/elabsheet/public/media \
    --exclude ".svn" \
    --exclude ".gitignore"
