#!/bin/bash

cd /home/pi/waterdetectionmodule
rm -rf env

python3 -m venv env

source env/bin/activate
pip install -r requirements.txt
deactivate
