#!/bin/bash
python3 ble-weather-monitor.py &
sleep 10   # better way???
gnuplot ble-plot.gp &
cd Dropbox/db_development/lang/py/flask
python3 flask_upload.py &
cd ~
./pushBLEdata.sh &
cd /home/cxd/Git/ble-weather-station-enhanced/phonegap
phonegap serve &
cd ~
