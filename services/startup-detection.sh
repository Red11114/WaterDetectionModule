#!/bin/bash

# activate the venv
cd /home/pi/WaterDetectionModule
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
python3 OperationDetect.py
python3 ina260.log.py