#!/bin/bash

HOME=/home/__ELAB_NAME__

# activate virtual environment
. $HOME/app/elabsheet/ve

export PATH=$PATH:$HOME/virtualenv/__ELAB_NAME__/bin:$HOME/app/elabsheet/bin

cd $HOME/app/elabsheet
nohup ./manage.py run_grader &
