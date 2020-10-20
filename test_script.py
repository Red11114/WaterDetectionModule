# This is a test script
from OperationDetect import SERIAL_PORT,SERIAL_RATE

try:
    # Import builtin packages
    import os, stat
    import logging
    from datetime import datetime
    import json
    import time as _time
    import threading
    print("WORKING: Import built in packages")
except:
    print("ERROR: Import built in packages")

try:
    # Import installed packages
    import RPi.GPIO as GPIO
    import serial
    import smbus
    print("WORKING: Import installed packages")
except:
    print("ERROR: Import installed packages")

try:
    # Import drivers
    from INA260_MINIMAL import INA260
    print("WORKING: Import drivers")
except:
    print("ERROR: Import drivers")

try:
    # Setup serial communication to the LTE modem
    ser = serial.Serial(SERIAL_PORT,SERIAL_RATE)
    print("WORKING: Serial is able to initialise")
except:
    print("ERROR: Serial is not able to initialise")

try:
    # Setup GPIO pins and define float/button pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
    GPIO.setup(22, GPIO.OUT, initial = GPIO.LOW) # Strobe pin
    print("WORKING: Communication to GPIO")
except:
    print("ERROR: No communication to GPIO")

print("TESTING: Strobe")
try:
    # Function to strobe the light
    i = 0
    count = 4
    secconds = 0.5
    while i < count:
        GPIO.output(22, GPIO.HIGH)
        _time.sleep(secconds)
        GPIO.output(22, GPIO.LOW)
        _time.sleep(secconds)
        i +=1
    sec = ""
    while sec == "":
        sec = input('CONFIRM: Confirm if the strobe activated yes/no/repeat')
        _time.sleep(0.6)
        if sec == "yes":
            print("WORKING: Strobe light confirmed")
            break
        elif sec == "no":
            print("ERROR: Strobe light not working")
            break
        elif sec == "repeat":
            print("REPEAT: Repeat strobe test")
except:
    print("ERROR: No communication to strobes GPIO")

print("TESTING: Float switch")
try:
	# Check if the float swich is high for the false_detect_time
    check_time = _time.perf_counter()
    false_detect_time = 2
    check = False
    while check == False and _time.perf_counter() > check_time - 30:
        while GPIO.input(17) == 0:
            if _time.perf_counter() - check_time > false_detect_time:
                check = True
                break
            _time.sleep(1)
    GPIO.output(22, GPIO.HIGH)
    _time.sleep(1)
    GPIO.output(22, GPIO.LOW)
    print("WORKING: Float switch functioning")
except:
    print("ERROR: Float switch not pressed in time")
    
print("TESTING: Button")
try:
	# Check if the float swich is high for the false_detect_time
    check_time = _time.perf_counter()
    false_detect_time = 2
    check = False
    while check == False and _time.perf_counter() > check_time - 30:
        while GPIO.input(27) == 0:
            if _time.perf_counter() - check_time > false_detect_time:
                check = True
                break
            _time.sleep(1)
    GPIO.output(22, GPIO.HIGH)
    _time.sleep(1)
    GPIO.output(22, GPIO.LOW)
    print("WORKING: Button functioning")
except:
    print("ERROR: Button not pressed in time")

try:
    # Open the setting file and read in the data
    with open('settings_.json') as json_file:
        settings = json.load(json_file)

    # Check the data for for required settings 
    for s in settings['settings']:
        ID = s['ID']
        NUM = s['NUM']
        print('ID loaded: ' + s['ID'])
        print('NUM loaded: ' + s['NUM'])
    print("WORKING: Settings file loaded")
except:
    print("ERROR: Settings file not loaded")

print("TESTING: 4G Modem communication")
try:
    OPERATE_SMS_MODE = 'AT+CMGF=1\r'
    ser.write(command.encode())
    _time.sleep(0.2)
    reply = ser.read(ser.in_waiting).decode()
    if reply.find("OK") != -1:
        print("WORKING: Communication with 4G Modem")
except:
    print("ERROR: No communication with 4G Modem")

print("TESTING: Please send a text to the module within")
try:
    print("TESTING: Please send a text to the module within 30 seconds")
    check_time = _time.perf_counter()
    reply = ""
    while reply.find("CMGL: ") != -1:
        # Open serial if required
        if not ser.is_open:
            ser.open()
        # Check if there is any unread texts
        sendCommand(RECEIVE_SMS)
        # sendCommand('\x1A')
        _time.sleep(0.2)
        reply = ser.read(ser.in_waiting).decode()
        _time.sleep(1)
        if _time.perf_counter() > check_time - 30:
            print("ERROR: SMS not sent in time")
            break
    if reply.find("CMGL: ") != -1:
        print("WORKING: SMS received")
except:
    print("ERROR: Unable to request SMS")
