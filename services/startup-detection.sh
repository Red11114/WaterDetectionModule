#!/bin/bash

# activate the venv
cd /home/pi/waterdetectionmodule
source env/bin/activate

# Create logs directory
# Check if logs directory does not exist
if [ ! -d "./logs" ] 
then
    echo "Directory logs DOES NOT exists."
    mkdir ./logs
else
    echo "Directory logs exists"
fi

# Run the main script
# python3 services/parallel_processing.py
python3 Beacon_Module.py