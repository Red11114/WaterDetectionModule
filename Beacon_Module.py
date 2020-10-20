#!/bin/bash
# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import builtin packages
import os, stat
import logging
from datetime import datetime
from datetime import date
import json
import time as _time
import threading

# Import installed packages
import RPi.GPIO as GPIO
import serial

# Import drivers
from INA260_MINIMAL import INA260

# Define At command strings
OPERATE_SMS_MODE = b'AT+CMGF=1\r'
RECEIVE_SMS = b'AT+CMGL="REC UNREAD"\r'
CLEAR_READ = b'AT+CMGD=1,1\r'
ALLOW_AIRPLANE_MODE = b'AT+QCFG="airplanecontrol",1\r'
MIN_FUNCTONALITY = b'AT+CFUN=0\r'
NORMAL_FUNCTONALITY = b'AT+CFUN=1\r'
DISABLE_SLEEP = b'AT+QSCLK=0\r'
ENABLE_SLEEP = b'AT+QSCLK=1\r'
ECHO_OFF = b'ATE0\r'
ENABLE_TIME_ZONE_UPDATE = b'AT+CTZU=3\r'
TIME_QUERY = b'AT+CCLK?\r'
SIGNAL_CHECK = b'AT+CSQ\r'
NETWORK_REG = b'AT+CREG=1\r'
AUTO_NETWORK = b'AT+COPS=0\r'
DISCONNECT_NETWORK = b'AT+COPS=2\r'

# Pin definitions
## hardware
FLOAT = 17
BUTTON = 27
STROBE = 22
## 3G LTE Modem
DTR = 13
W_DISABLE = 19
PERST = 26

# Function to load in settings from a json file
def load_settings():
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
	return ID, NUM

# Function to write settings to a json file
def write_settings(ID,NUM):
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

# no logging allowed in this function
def sync_LTE(ser):
	GPIO.output(DTR,GPIO.LOW)

	if not ser.is_open:
		ser.open()
		print("opening serial")

	active = checkActive(ser,40)

	if active == True:



		ser.write(NORMAL_FUNCTONALITY)
		_time.sleep(1)

		print(ser.read(ser.in_waiting))
		_time.sleep(0.5)
		signal = b'99'

		while signal == b'99':
			ser.write(SIGNAL_CHECK)
			_time.sleep(0.5)
			chunk = ser.read(ser.in_waiting)
			print(chunk)
			if b'OK' in chunk:
				signal = chunk[8:-11]
				print(signal)

		ser.write(DISCONNECT_NETWORK)
		_time.sleep(0.3)

		print(ser.read(ser.in_waiting))
		_time.sleep(0.3)

		ser.write(ENABLE_TIME_ZONE_UPDATE)
		_time.sleep(0.3)

		print(ser.read(ser.in_waiting))
		_time.sleep(0.3)

		ser.write(NETWORK_REG)
		_time.sleep(0.3)

		print(ser.read(ser.in_waiting))
		_time.sleep(0.3)

		ser.write(AUTO_NETWORK)
		_time.sleep(0.3)

		print(ser.read(ser.in_waiting))
		_time.sleep(0.3)

		ser.write(TIME_QUERY)
		_time.sleep(0.3)

		modem_time = ser.read(ser.in_waiting)
		print(modem_time)

		if b'OK' in modem_time:
			modem_time = modem_time[10:27].decode()
			print(modem_time)
			modem_time = datetime.strptime(modem_time, '%y/%m/%d,%H:%M:%S')
			print(modem_time)
		else:
			print("failed to get time")
		# read_buffer=[]
		# while ser.in_waiting != 0:
		# 	chunk=ser.readline()[:-2]	# remove the '\r\n'
		# 	read_buffer.append(chunk.decode())
		# ser.close()
		# print(read_buffer)

		pi_clock = datetime.now()
		print("Pi clock time: %s" % pi_clock)
	
		try:
			
			print("local time: %s" % local_time)
			#print(local_time.month)
			#utc_time =  local_time.strftime("%Y-%m-%d %H:%M:%S")
			#local_time.year + local_time.month + local_time.day + "" + local_time.hour + ":" + local_time.minute + ":" + local_time.second
			#print("Utc time: %s" % utc_time)
			print(_time.ctime())
			cmd = 'sudo date --set "%s"' % local_time
			print("cmd = %s" % cmd)
			os.system(cmd)
			print(_time.ctime())
			pi_clock = datetime.now()
			print("Pi clock time: %s" % pi_clock)

			return local_time
		except:
			print("failed to set time")
	return None

def sleep_LTE(ser):
	# set SMS module to sleep
	if not ser.is_open:
		ser.open()

	active = checkActive(ser,60)

	if active == True:
		print("Going into sleep mode")
		logging.info("Going into sleep mode")

		sendCommand(ser,MIN_FUNCTONALITY)
		readResponse(ser)
		sendCommand(ser,ENABLE_SLEEP)
		readResponse(ser)

		ser.close()
		GPIO.output(DTR, GPIO.HIGH)
		_time.sleep(0.1)
	else:
		print("Unable to go into sleep mode: device unresponsive")
		logging.error("Unable to go into sleep mode: device unresponsive")

def wake_LTE(ser):
	# set all devices to be active
	GPIO.output(DTR,GPIO.LOW)

	print("Returing from sleep mode")
	logging.info("Returing from sleep mode")

	active = checkActive(ser,60)

	if active == True:
		sendCommand(ser,NORMAL_FUNCTONALITY)
		readResponse(ser)
		_time.sleep(0.3)
		logging.info('SMS module is now active')
	else:
		logging.error('SMS module was unable to wake from sleep')

def checkActive(ser,time_out):
	temp_time = _time.perf_counter()
	active = b''
	print("Check modem is active")
	if not ser.is_open:
		ser.open()

	while (_time.perf_counter() - time_out < temp_time):
		ser.write(b'AT\r')
		_time.sleep(0.3)
		active = ser.read(ser.in_waiting)
		_time.sleep(0.3)
		print(active)
		if active.find(b'OK') != -1:
			print("Modem active")
			return True
	print("Modem inactive")
	return False

# Function for sending AT commands
def sendCommand(ser,command):
	if not ser.is_open:
		ser.open()

	logging.info("MODEM COMMAND: %s" % command.decode())
	print("MODEM COMMAND: %s" % command.decode())

	ser.write(command)
	_time.sleep(0.3)
	ser.readline()
	_time.sleep(0.1)

def readResponse(ser):
	# Read all characters on the serial port and return them.
	if not ser.timeout:
		raise TypeError('Port needs to have a timeout set!')

	# ser.reset_input_buffer()
	read_buffer=[]
	# print("num in waiting = %d" % ser.in_waiting)
	while ser.in_waiting != 0:
		chunk=ser.readline()[:-2]	# remove the '\r\n'
		read_buffer.append(chunk.decode())
	ser.close()

	for lines in read_buffer:
		logging.info('MODEM RESPONSE: %s' % lines)
		print("MODEM RESPONSE: %s" % lines)

	return read_buffer

# Function for sending a Text
def send_txt(ser,message,number):
	SEND_SMS = b'AT+CMGS="%s"\r'% number

	wake_LTE()

	active = checkActive(ser,10)
	if active == True:
		logging.info("Sending SMS, %s : %s" % (number,message))
		print("Sending SMS to, %s : %s" % (number,message))
		sendCommand(ser,OPERATE_SMS_MODE)
		readResponse(ser)
		sendCommand(ser,SEND_SMS)
		readResponse(ser)
		sendCommand(ser,message)
		readResponse(ser)
		sendCommand(ser,'\x1A')	#sending CTRL-Z not sure if needed
		readResponse(ser)
	else:
		logging.info("Unable to send SMS: module unresponsive, %s : %s" % (number,message))
		print("Unable to send SMS: module unresponsive, %s : %s" % (number,message))

	sleep_LTE()

# Function for receiving a Text.
# will respond accordingly?
def receive_txt():
	# logging.info("Attempt to receive text")
	# Open serial if required
	if not ser.is_open:
		# logging.info("Open serial")
		ser.open()
	# Check if there is any unread texts
	sendCommand(ser,RECEIVE_SMS)
	# sendCommand('\x1A')
	_time.sleep(0.2)
	reply = ser.read(ser.in_waiting).decode()
	# Split the reply inot individual responses
	reply_lines = reply.split("\n")
	print("MODEM Response: %s" % reply_lines)
	# logging.info("MODEM Response: %s" % reply_lines)
	# Check if the reply contains a received SMS
	if reply.find("CMGL: ") != -1:
		# logging.info('Found CMGL: in serial response')

		print("Reply_lines %s" % reply_lines)
		# Find index of response that contains the SMS
		for i in range(len(reply_lines)):
			if reply_lines[i].find("CMGL: ") != -1:
				response_index = i
				print("response at index: %s"% i)
		# Extract the SMS info
		info_list = reply_lines[response_index]
		# logging.info('SMS info list from serial: %s' % info_list)
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
		# logging.info("TEXT: %s" % text_msg)
		print("TEXT: %s" % text_msg)
		# Clear the modems SMS memory
		sendCommand(CLEAR_READ)
		reply = ser.read(ser.in_waiting)
		return number, text_msg
	return None,None

# # Fucntion to start a timer while waiting for a response
# def receive_confirmation(timer):
# 	global ID
# 	global confirming
# 	# Begin timer for how long to wait for confirmation
# 	confirming = True
# 	# logging.info("Starting timer for %s seconds" % timer)
# 	time = _time.perf_counter()
# 	while _time.perf_counter() < time + timer:
# 		# Create count down
# 		clock = timer - (_time.perf_counter() - time)
# 		# logging.info("Countdown: %d" % clock)
# 		print("Countdown: %d" % clock)
# 		txt_number, txt_msg = receive_txt()
# 		if txt_msg != None:
# 			# Check if the Modules ID number is included
# 			if (txt_msg.find(ID) != -1):
# 				# logging.info("Received confirmation reply: %s" % txt_msg)
# 				# Check what command was sent
# 				if (txt_msg.find("yes") != -1) or (txt_msg.find("Yes") != -1):
# 					confirming = False
# 					# logging.info('Confirmed yes')
# 					strobe_light(0.2,5)
# 					return True
# 				elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
# 					confirming = False
# 					logging.info('Confirmed no')
# 					return False
# 				else:
# 					# logging.warning("Confirmation not correctly spelt")
# 					send_txt('Confirmation spelt incorrectly',txt_number)
# 			else:
# 				# logging.warning('Incorrect format, reply: %s yes/no' % ID)
# 				send_txt('Incorrect format, reply: %s yes/no' % ID,txt_number)
# 		_time.sleep(1)
# 	# logging.info("TIMER OUT")
# 	confirming = False
# 	return None

# Function to strobe the light
def strobe_light(secconds, count):
	# logging.info("Strobe light :)")
	i = 0
	while i < count:
		GPIO.output(STROBE, GPIO.HIGH)
		_time.sleep(secconds)
		GPIO.output(STROBE, GPIO.LOW)
		_time.sleep(secconds)
		i +=1

# Alerts the user by SMS
def check_float():
	# initialise active check time
	temp_time = _time.perf_counter()
	false_detect_time = 5
	# Check if the float swich is high for the false_detect_time
	while GPIO.input(17) == 0:
		if _time.perf_counter() - temp_time > false_detect_time:
			logging.info("The float was activated for %s seconds" % false_detect_time)
			strobe_light(0.5,4)

			return True
		_time.sleep(0.5)
	return False

def check_button():
	# initialise active check time
	temp_time = _time.perf_counter()
	false_detect_time = 4
	# Check if the button is high for the false_detect_time
	while GPIO.input(27) == 0:
		if _time.perf_counter() - temp_time > false_detect_time:
			# logging.info("The button was held for at least %s seconds when the device was booted" % false_detect_time)
			strobe_light(0.2,4)
			return True
		_time.sleep(0.5)
	return False

def check_voltage(ina260):
	voltage = ina260.get_bus_voltage()
	current = ina260.get_current()

	print(voltage,current)
	logging.debug('V=%f,I=%f' % (voltage,current))

	return voltage, current

def warmup():
	# Setup GPIO pins and define float/button pins
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(FLOAT, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
	GPIO.setup(DTR, GPIO.OUT, initial=GPIO.HIGH) # DTR pin on 4g module
	GPIO.setup(W_DISABLE, GPIO.OUT, initial=GPIO.LOW) # W_DISABLE pin on 4g module
	GPIO.setup(PERST, GPIO.OUT, initial=GPIO.LOW) # PERST pin on 4g module
	GPIO.setup(STROBE, GPIO.OUT, initial=GPIO.LOW) # Strobe pin

	# Serial settings
	SERIAL_PORT = '/dev/ttyAMA0'
	SERIAL_RATE = 115200

	# Setup serial communication to the LTE modem
	ser = serial.Serial(port=SERIAL_PORT,baudrate=SERIAL_RATE,timeout=2,write_timeout=2)

	local_time=sync_LTE(ser)
	if local_time != None:
		# Setup logging
		print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (local_time.day,local_time.month,local_time.year,local_time.hour,local_time.minute,local_time.second))
		try:
			logging.basicConfig(filename='logs/%s-%s-%s_%s-%s-%s.log' % (local_time.day,local_time.month,local_time.year,local_time.hour,local_time.minute,local_time.second), filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
			logging.info('Log file has been created: logs/%s-%s-%s_%s-%s-%s.log' % (local_time.day,local_time.month,local_time.year,local_time.hour,local_time.minute,local_time.second))
		except:
			print("Log file could not be made")
	else:
		print("Modem was unable to sync time")
		try:
			logging.basicConfig(filename='logs/PI_CLK.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
		except:
			print("unable to create logfile using Pi's Clock")

	active = checkActive(ser,40)
	if active == True:
		# Configure modem settings
		logging.info("Setup modem settings")
		sendCommand(ser,ECHO_OFF) # removes echo
		readResponse(ser)
		sendCommand(ser,ALLOW_AIRPLANE_MODE)
		readResponse(ser)

		# Put the LTE module to sleep to save power
		sleep_LTE(ser)
	else:
		logging.error("Unable to setup modem settings: device unresponsive")

	logging.info("Initialise and reset INA260 chip")
	ina260 = INA260(dev_address=0x40)
	ina260.reset_chip()
	_time.sleep(0.1)

	logging.info('Warmup has been completed')
	return ina260, ser

# MAIN gets called on script startup
def main():
	ina260,ser=warmup()
	if check_button() == True:
		send_txt('Button held during startup, entering configuration mode on module %s' % ID,NUM)
		strobe_light(1,10)
		temp_time = _time.perf_counter()
		time_out = 5*60
		while (_time.perf_counter() - time_out) < temp_time:
			print()
			# do somthing to promt user for change of phone number/module number
			# restart after exiting config mode if any settings have been changed

	# Load settings from settings_.json
	ID, NUM = load_settings()

	while True:
		# check water sensor
		if check_float() == True:
			send_txt('Float switch has been activated on module %s' % ID,NUM)

		temp_voltage, temp_current = check_voltage(ina260)
		if temp_voltage > 12.2:
			warned = False
		elif temp_voltage <= 11.80:
			logging.warning("Voltage LOW: %sV" % temp_voltage)
		elif temp_voltage <= 11.60 :
			if warned == False:
				send_txt("Module %s, Low Battery Warning: %sV" % (ID,temp_voltage),NUM)
				warned = True
			logging.warning("Voltage VERY LOW: %sV" % temp_voltage)
		_time.sleep(60*10)

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
