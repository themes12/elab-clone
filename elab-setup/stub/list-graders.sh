#!/bin/bash

if [ -z $1 ]; then
  ELABUSER=$(whoami)
else
  ELABUSER=$1
fi
ps -ef | grep -v grep | grep "$ELABUSER .* run_grader" | awk '{print $2}'
