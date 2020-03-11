#!/bin/bash

cd /home/pi/WaterDetectionModule
rm -rf env

python3 -m venv env

source env/bin/activate
pip install -r requirements.txt
deactivate