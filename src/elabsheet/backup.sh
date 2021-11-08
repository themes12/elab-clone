#!/bin/sh

BACKUP_DIR=~/backup
STAMP=`date +%b%d-%y`
DB_FILE=${BACKUP_DIR}/db.${STAMP}.sql.gz
MEDIA_FILE=${BACKUP_DIR}/media.${STAMP}.tar.gz

echo "Creating database backup ${DB_FILE}..."
mysqldump -u elab -p elab | gzip -c > ${DB_FILE}

echo "Creating media&supplements backup ${MEDIA_FILE}..."
tar zcf ${MEDIA_FILE} media/eqn media/supplements \
    --exclude ".svn" \
    --exclude ".gitignore"
