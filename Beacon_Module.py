#!/bin/bash
# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import builtin packages
import os, stat
import logging
from datetime import datetime
import json
import time as _time
import threading

# Import installed packages
import RPi.GPIO as GPIO
import serial

# Import drivers
from INA260_MINIMAL import INA260

ID = ""
NUM = ""

# Define At command strings
OPERATE_SMS_MODE = 'AT+CMGF=1\r'
RECEIVE_SMS = 'AT+CMGL="REC UNREAD"\r'
CLEAR_READ = 'AT+CMGD=1,1'
TURN_ON_AIRPLANE_MODE = 'AT+QCFG=”airplanecontrol”,1'

# Serial settings
SERIAL_PORT = '/dev/ttyUSB2'
SERIAL_RATE = 115200

# Setup serial communication to the LTE modem
ser = serial.Serial(SERIAL_PORT,SERIAL_RATE)

# Setup GPIO pins and define float/button pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
GPIO.setup(33, GPIO.OUT, initial=GPIO.HIGH) # DTR pin on 4g module
GPIO.setup(35, GPIO.OUT, intital=GPIO.LOW) # W_DISABLE pin on 4g module
GPIO.setup(37, GPIO.OUT, intital=GPIO.LOW) # PERST pin on 4g module
GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW) # Strobe pin

# Function to load in settings from a json file
def load_settings():
	global NUM
	global ID
	logging.info("Loading settings")
	# Open the setting file and read in the data
	with open('settings_.json') as json_file:
		settings = json.load(json_file)
	# Check the data for for required settings 
	for s in settings['settings']:
		ID = s['ID']
		NUM = s['NUM']
		logging.info('ID loaded: ' + s['ID'])
		logging.info('NUM loaded: ' + s['NUM'])

# Function to write settings to a json file
def write_settings():
	global NUM
	global ID
	logging.info("Saving settings: ID - %s, NUM - %s" %(ID,NUM))
	# Initialize data structre to be saved to file
	data = {}
	data['settings'] = []
	data['settings'].append({
		'ID': ID,
		'NUM': NUM
	})
	# Open file amd save data
	with open('settings_.json', 'w') as outfile:
		json.dump(data, outfile,indent=4)

def sleep_LTE(time):
	# set SMS module to sleep
	GPIO.output(35, GPIO.HIGH)
	_time.sleep(0.1)
	GPIO.output(35, GPIO.LOW)
	_time.sleep(time)
	

def wake_LTE():
	# set all devices to be active
	strobe_light(0.1,2)

	GPIO.output(33,GPIO.LOW)
	_time.sleep(0.1)
	GPIO.output(33,GPIO.HIGH)

	if not ser.is_open:
		print("open serial")
		ser.open()
	
	sendCommand(OPERATE_SMS_MODE)
	# sendCommand(CLEAR_READ)
	ser.read(ser.in_waiting) # should not need this?
	logging.info('SMS module is active has been completed')


def warmup():
	logging.info("Start warmup")

	logging.info("Initialise and reset INA260 chip")
	global ina260
	ina260 = INA260(dev_address=0x40)
	ina260.reset_chip()
	_time.sleep(1)
	
	# Setup logging
	# Add polling for real time?
	datetime_object = datetime.now()
	print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second))
	try:
		logging.basicConfig(filename="logs/%s-%s-%s:%s-%s-%s_Operation.log" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second), filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	except:
		print("Log file could not be made")
		logging.error("Log file could not be made")

	# Load settings from settings_.json
	load_settings()
	
	strobe_light(0.1,2)

	if not ser.is_open:
		print("open serial")
		ser.open()
	# if the LTE module doesnt activate, reset it?

	# sendCommand(OPERATE_SMS_MODE)
	# sendCommand(CLEAR_READ)
	ser.read(ser.in_waiting) # should not need this?
	# logging.info('Turn on airplane mode')
	# # sendCommand(TURN_ON_AIRPLANE_MODE)
	response = ser.read(ser.in_waiting)
	logging.info(response)
	print(response)
	logging.info('Warmup has been completed')
	
# Function for sending AT commands
def sendCommand(command): 
	ser.write(command.encode())
	# logging.info("Send command to LTE module %s" % command)
	_time.sleep(0.2)

# Function for sending a Text
def send_txt(message,number):
	SEND_SMS = 'AT+CMGS="%s"\r'% number
	logging.info("Sending SMS to %s"% number)
	print("Sending SMS to %s"% number)
	# Open serial if required
	if not ser.is_open:
		logging.info("Open serial")
		ser.open()
	# Send the SMS
	if ser.is_open:
		logging.info("SMS SENT: %s" % message)
		print("SMS SENT: %s" % message)
		# sendCommand(OPERATE_SMS_MODE)
		# sendCommand(SEND_SMS)
		# sendCommand(message)
		# sendCommand('\x1A')	#sending CTRL-Z
		ser.close()
		logging.info("close serial")

# Function for receiving a Text. 
# will respond accordingly?
def receive_txt():
	# logging.info("Attempt to receive text")
	# Open serial if required
	if not ser.is_open:
		logging.info("Open serial")
		ser.open()
	# Check if there is any unread texts
	sendCommand(RECEIVE_SMS)
	# sendCommand('\x1A')
	_time.sleep(0.2)
	reply = ser.read(ser.in_waiting).decode()
	# Split the reply inot individual responses
	reply_lines = reply.split("\n")
	print("MODEM Response: %s" % reply_lines)
	# logging.info("MODEM Response: %s" % reply_lines)
	# Check if the reply contains a received SMS
	if reply.find("CMGL: ") != -1:
		logging.info('Found CMGL: in serial response')
		
		print("Reply_lines %s" % reply_lines)
		# Find index of response that contains the SMS
		for i in range(len(reply_lines)):
			if reply_lines[i].find("CMGL: ") != -1:
				response_index = i
				print("response at index: %s"% i)
		# Extract the SMS info
		info_list = reply_lines[response_index]
		logging.info('SMS info list from serial: %s' % info_list)
		info_list = info_list.split(",")
		print("Info_list: %s" % info_list)
		# Find number of txts in mem, the sender's number and the text msg
		txt_num = info_list[0]
		txt_num = txt_num[len(txt_num)-1:len(txt_num)]
		print("NUMBER OF TXTS: %s" % txt_num)
		number = info_list[2]
		number = number[1:len(number)-1]
		print("NUMBER: %s" % number)
		text_msg = reply_lines[response_index+1]
		logging.info("TEXT: %s" % text_msg)
		print("TEXT: %s" % text_msg)
		# Clear the modems SMS memory
		sendCommand(CLEAR_READ)
		reply = ser.read(ser.in_waiting)
		return number, text_msg
	return None,None

# Fucntion to start a timer while waiting for a response
def receive_confirmation(timer):
	global ID
	global confirming
	# Begin timer for how long to wait for confirmation
	confirming = True
	logging.info("Starting timer for %s seconds" % timer)
	time = _time.perf_counter()
	while _time.perf_counter() < time + timer:
		# Create count down
		clock = timer - (_time.perf_counter() - time)
		logging.info("Countdown: %d" % clock)
		print("Countdown: %d" % clock)
		txt_number, txt_msg = receive_txt()
		if txt_msg != None:
			# Check if the Modules ID number is included
			if (txt_msg.find(ID) != -1):
				logging.info("Received confirmation reply: %s" % txt_msg)
				# Check what command was sent
				if (txt_msg.find("yes") != -1) or (txt_msg.find("Yes") != -1):
					confirming = False
					logging.info('Confirmed yes')
					strobe_light(0.2,5)
					return True
				elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
					confirming = False
					logging.info('Confirmed no')
					return False
				else:
					logging.warning("Confirmation not correctly spelt")
					send_txt('Confirmation spelt incorrectly',txt_number)
			else:
				logging.warning('Incorrect format, reply: %s yes/no' % ID)
				send_txt('Incorrect format, reply: %s yes/no' % ID,txt_number)
				
		_time.sleep(1)
	logging.info("TIMER OUT")
	confirming = False
	return None

# Function to strobe the light
def strobe_light(secconds, count):
	logging.info("Strobe light :)")
	i = 0
	while i < count:
		GPIO.output(22, GPIO.HIGH)
		_time.sleep(secconds)
		GPIO.output(22, GPIO.LOW)
		_time.sleep(secconds)
		i +=1

# Alerts the user by SMS
def check_float():
	# initialise active check time
	check_time = _time.perf_counter()
	false_detect_time = 20
	# Check if the float swich is high for the false_detect_time
	while GPIO.input(17) == 0:
		if _time.perf_counter() - check_time > false_detect_time:
			logging.info("The float was activated for %s seconds" % false_detect_time)
			strobe_light(0.5,4)
			
			return True
		_time.sleep(1)
	return False
		
def check_button():
	# initialise active check time
	check_time = _time.perf_counter()
	false_detect_time = 5
	# Check if the button is high for the false_detect_time
	while GPIO.input(27) == 0:
		if _time.perf_counter() - check_time > false_detect_time:
			logging.info("The button was held for at least %s seconds when the device was booted" % false_detect_time)
			strobe_light(0.5,4)
			return True
		_time.sleep(1)
	return False

	# The button is considered pressed
	# if check == True:
	# 	strobe_light(0.1,2)
	# 	send_txt('Button has been pressed on module %s, Do you wish to reset the Float switch? Reply: %s yes/no, within %s minutes' % (ID, ID, confirmation_time),NUM)
	# 	# Start a confirmation receive for x seconds
	# 	confirmation = receive_confirmation(confirmation_time*60)
	# 	if confirmation == True:
	# 		print("Resetting the float switch detection")
	# 		try:
	# 			GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500) 
	# 			logging.info("Event detect enabled for float switch")
	# 			send_txt('Float switch has been activated',NUM)
	# 		except:
	# 			logging.warning("Event detect could not be enabled for float switch")
	# 			pass
	# 	elif confirmation == False:
	# 		send_txt('Reset Declined',NUM)
	# 	elif confirmation == None:
	# 		send_txt('Timer ran out',NUM)

# MAIN gets called on script startup
def main():
	global ID
	global NUM
	global confirming
	global ina260

	warmup()
	
	warned = False
	temp_voltage = ina260.get_bus_voltage()
	config_mode=check_button()

	if config_mode == True:
		strobe_light(1,10)
		send_txt('Button held during startup, entering configuration mode on module %s' % ID,NUM)
		# do somthing to promt user for change of phone number/module number
		# restart after exiting config mode if any settings have been changed
	else:
		strobe_light(0.5,2)

	while True:
		
		# check water sensor
		if check_float() == True:
			strobe_light(2,1)
			# wake_LTE()
			send_txt('Float switch has been activated on module %s' % ID,NUM)
			# sleep_LTE()
		else:
			strobe((0.2,1))

		current_voltage = ina260.get_bus_voltage()
		# Check Voltage and send text if low
		if current_voltage < temp_voltage - 0.1:
			if current_voltage > 12.4:
				warned = False
			elif current_voltage <= 11.80:
				logging.warning("Voltage LOW: %s" % current_voltage)
			elif current_voltage <= 11.60 :
				if warned == False:
					# wake_LTE()
					send_txt("Module %s: Low Battery Warning-%sV" % (ID,current_voltage),NUM)
					# sleep_LTE()
					warned = True
				logging.warning("Voltage VERY LOW: %s" % current_voltage)
			else:
				logging.info("Voltage: %s" % current_voltage)
			# Assign new temp voltage
			temp_voltage = ina260.get_bus_voltage()
		
		_time.sleep(10)
		
		# print("waiting for SMS")
		# logging.info("Waiting for SMS, Voltage: %0.2f" % current_voltage)
		# # check if there has been a text received
		# # check if there has been a text received
		# txt_number, txt_msg = receive_txt()
		# if txt_msg != None:
		# 	# make sure the text include the modules ID
		# 	if txt_msg.find(ID) != -1:
		# 		logging.info("Text has correct ID for module")
		# 		# check if the text includes "change" or "status"
		# 		if txt_msg.find("change") != -1 or txt_msg.find("Change") != -1:
		# 			logging.info("Change number requested")
		# 			# Find the number after the "#"
		# 			if txt_msg.find("#") != -1:
		# 				new_num = txt_msg.split("#")
		# 				new_num = new_num[len(new_num)-1]
		# 				new_num = new_num[0:12]
		# 				print("Number :%s" % new_num)
		# 				# Check if the format of the number is correct
		# 				if len(new_num) == len(NUM) and new_num.find('+614') != -1: 
		# 					send_txt('Setting main number on module %s to %s. Confirm: 0001 yes/no within 1 minute' % (ID, new_num), txt_number)
		# 					# Start a confirmation receive for x seconds
		# 					strobe_light(0.5,1)
		# 					confirmation = receive_confirmation(60)
		# 					if confirmation == True:
		# 						send_txt('Number Change Accepted for module %s, new number: %s' % (ID, new_num), txt_number)
		# 						NUM = new_num
		# 						write_settings()
		# 						print("New Number set to %s" % NUM)
		# 					elif confirmation == False:
		# 						send_txt('Number Change Declined for module %s' % ID, txt_number)
		# 					elif confirmation == None:
		# 						send_txt('Timer ran out when changing number for module %s' % ID, txt_number)
		# 				else:
		# 					send_txt('The number specified does not meet the required format: +614xxxxxxxx', txt_number)
		# 			else:
		# 				send_txt('For a number change request please use the following format: %s change #+614number' % ID, txt_number)
		# 		elif txt_msg.find("status") != -1 or txt_msg.find("Status") != -1:
		# 			logging.info("Status requested")
		# 			strobe_light(0.5,1)
		# 			# Return status of the device
		# 			if GPIO.input(17) == 0:
		# 				send_txt('Status Report for module %s: Voltage=%0.2f, Float switch triggered, Saved number is %s' % (ID,current_voltage,NUM), txt_number)
		# 			elif GPIO.input(17) == 1:
		# 				send_txt('Status Report for module %s: Voltage=%0.2f, Float switch not triggered, Saved number is %s' % (ID,current_voltage,NUM), txt_number)
		# 			else:
		# 				send_txt('Status Report for module %s: Voltage=%0.2f, Float switch in undefined state please check and restart the device, Saved number is %s' % (ID,current_voltage,NUM), txt_number)
		# 		else:
		# 			print("Correct ID(%s) received but command not recognised" % ID)
		# 			logging.warning("Correct ID(%s) received but command not recognised" % ID)
		# 			send_txt('Correct ID(%s) received but the command was not recognised, Commands: change, status'% ID,txt_number)
		

if __name__ == "__main__":
	try:
		main()
	except ValueError as e:
		logging.info("Error : {}".format(e))