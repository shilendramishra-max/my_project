#!/bin/bash
. $HOME/.bash_profile
source /home/sdlreco/crons/config/recon.sh

#conda activate pyreco_3.9_v1.1

now=`date +"%Y-%m-%d"`
LCK_FILE=/home/sdlreco/crons/ybl_aeps/usage/check_usage-${now}.lck
if [ ! -f $LCK_FILE ];
then
touch $LCK_FILE
python /home/sdlreco/crons/ybl_aeps/ybl_aeps.py 1>>/home/sdlreco/crons/ybl_aeps/out/out-${now}.txt 2>>/home/sdlreco/crons/ybl_aeps/error/error-${now}.txt
else
echo "Previous Reconciliation still running"
fi






