#!/bin/bash

HOME=/home/__ELAB_NAME__
LOGFILE=$HOME/logs/grader.log
NUM_GRADERS=5
USER=$(whoami)

cur_graders=$(./list-graders.sh | wc -l)
to_spawn=$[ $NUM_GRADERS-$cur_graders ]

if [ $to_spawn -gt 0 ]; then
    echo "[$(date +'%F %T')] $cur_graders grader(s) are running, restarting $to_spawn grader(s)" >> $LOGFILE
    i=0
    while [ $i -lt $to_spawn ]
    do
        $HOME/start-grader.sh
        ((i++))
    done
fi
