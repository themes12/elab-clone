#!/bin/bash
 
NAME="__ELAB_NAME__"                                    # Name of the application
DJANGODIR=/home/__ELAB_NAME__/app/elabsheet             # Django project directory
ENVDIR=/home/__ELAB_NAME__/virtualenv/__ELAB_NAME__     # Virtual environment directory
#SOCKFILE=/home/elab/app/elabsheet/run/gunicorn.sock  # we will communicate using this unix socket
URL=__GUNICORN_IP__:__GUNICORN_PORT__				  # listen port
USER=__ELAB_NAME__                                         # the user to run as
GROUP=__ELAB_NAME__                                        # the group to run as
NUM_WORKERS=3                                     # how many worker processes should Gunicorn spawn
TIMEOUT=30
DJANGO_SETTINGS_MODULE=elabsheet.settings         # which settings file should Django use
DJANGO_WSGI_MODULE=elabsheet.wsgi                 # WSGI module name
ERROR_LOGFILE=/home/__ELAB_NAME__/logs/elab.log	          # gunicorn's error logfile
 
echo "[`date`] Starting $NAME as `whoami`"
 
# Activate the virtual environment
cd $ENVDIR
source bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
export PATH=$PATH:$DJANGODIR/bin
 
# Create the run directory if it doesn't exist
#RUNDIR=$(dirname $SOCKFILE)
#test -d $RUNDIR || mkdir -p $RUNDIR
 
# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
#exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
#Eexec bin/gunicorn ${DJANGO_WSGI_MODULE} \
#  --name $NAME \
#  --workers $NUM_WORKERS \
#  --user=$USER --group=$GROUP \
#  --bind=unix:$SOCKFILE \
#  -b $URL \
#  --log-level=debug \
#  --log-file=-

cd $DJANGODIR
gunicorn ${DJANGO_WSGI_MODULE} \
  -b $URL \
  --name $NAME \
  --workers $NUM_WORKERS \
  --timeout $TIMEOUT \
  --user=$USER --group=$GROUP \
  --error-logfile $ERROR_LOGFILE
