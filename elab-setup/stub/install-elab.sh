#!/bin/bash

HOME_DIR=/home/__ELAB_NAME__
ELAB_DIR=${HOME_DIR}/app/elabsheet

if [ "$1" = "--docker" ]; then
  DOCKER=1
else
  DOCKER=0
fi

if [ $DOCKER = 0 ]; then
  echo "*** Downloading elab ***"
  su -c "git clone https://gitlab.com/cjaikaeo/elabsheet.git ${ELAB_DIR}" __ELAB_NAME__

  echo "*** Copying configurations ***"
  su -c "
    cp settings_local.py ${ELAB_DIR}/elabsheet/
    chmod go-rwx ${ELAB_DIR}/elabsheet/settings_local.py
    cp backup.sh start-grader.sh check-graders.sh list-graders.sh gunicorn-start-elab.sh ${HOME_DIR}
    (
      cd ${HOME_DIR}
      chmod a+x start-grader.sh check-graders.sh list-graders.sh gunicorn-start-elab.sh
      chown __ELAB_NAME__:__ELAB_NAME__ start-grader.sh check-graders.sh list-graders.sh gunicorn-start-elab.sh
    )
    cp tqfauthen.py ${ELAB_DIR}/lab/backends/
    chown __ELAB_NAME__:__ELAB_NAME__ ${ELAB_DIR}/lab/backends/tqfauthen.py
  " __ELAB_NAME__

  echo "*** Setting up elab working directory ***"
  su -c "
    cd ${ELAB_DIR}
    ./install-dirs.sh
  " __ELAB_NAME__
  
  (
    cd ${ELAB_DIR}
    ./install-box.sh
  )

  su -c "
    cd ${ELAB_DIR}
    ln -s ${HOME_DIR}/virtualenv/__ELAB_NAME__/bin/activate ve
    . ./ve
    pip install -r requirements.txt --ignore-installed --force-reinstall --upgrade --no-cache-dir
    pip install --no-cache-dir 'gunicorn>=19.9,<19.10' 'django-auth-ldap>=1.6.1,<1.7'
    ./manage.py migrate
    ./collectstatic.sh
  " __ELAB_NAME__
else
  cp ../../requirements.txt ${HOME_DIR}
  cp gunicorn-start-elab.sh ${HOME_DIR}
  chmod a+x ${HOME_DIR}/gunicorn-start-elab.sh
  chown __ELAB_NAME__:__ELAB_NAME__ requirements.txt gunicorn-start-elab.sh
  su -c "
    cd ${HOME_DIR}
    . ${HOME_DIR}/virtualenv/__ELAB_NAME__/bin/activate ve
    pip install -r requirements.txt --ignore-installed --force-reinstall --upgrade --no-cache-dir
    pip install --no-cache-dir 'gunicorn>=19.9,<19.10' 'django-auth-ldap>=1.6.1,<1.7'
  " __ELAB_NAME__
fi
