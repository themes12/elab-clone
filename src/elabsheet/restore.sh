#!/bin/bash

BACKUP_DIR=/home/elab/backup

show_usage()
{
    echo "Usage: $0 [--skip-db] [--skip-media] <time-stamp>"
    echo "Available backup timestamps:"
    ls ${BACKUP_DIR}/db.* | sed 's/^.*db\.\(.*\)\.sql\.gz/  \1/'
}

# Process options and timestamp argument
SKIP_DB=0
SKIP_MEDIA=0
while [ $1 ]; do
    if [ "$1" = "--skip-db" ]; then
        SKIP_DB=1
    elif [ "$1" = "--skip-media" ]; then
        SKIP_MEDIA=1
    else
        STAMP=$1
        shift
        break
    fi
    shift
done

if [ -z "$STAMP" -o "$1" ]; then
    show_usage
    exit 1
fi

if [ $UID != 0 ]; then
    echo 'This script must be run as root.'
    exit 2
fi

DB_FILE=${BACKUP_DIR}/db.${STAMP}.sql.gz
MEDIA_FILE=${BACKUP_DIR}/media.${STAMP}.tar.gz
if [ ${SKIP_DB} = 0 ]; then
    if [ -f ${DB_FILE} ]; then
        echo "Restoring database..."
        echo "Please provide MySQL database password for elab"
        gunzip -c ${DB_FILE} | mysql -u elab -p elab
    else
        echo "Database file '${DB_FILE}' not found"
    fi
fi

if [ ${SKIP_MEDIA} = 0 ]; then
    if [ -f ${MEDIA_FILE} ]; then
        echo "Restoring media and supplements..."
        echo "Please provide account password"
        rm -rf media/eqn media/supplements
        tar zxf ${MEDIA_FILE} 
    else
        echo "Media and supplements file '${MEDIA_FILE}' not found"
    fi
fi
