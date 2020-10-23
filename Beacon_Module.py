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
from EC25_Driver import smsModem

# Define At command strings
OPERATE_SMS_MODE = b'AT+CMGF=1\r'
RECEIVE_SMS = b'AT+CMGL="REC UNREAD"\r'
CLEAR_READ = b'AT+CMGD=1,1\r'
ALLOW_AIRPLANE_MODE = b'AT+QCFG="airplanecontrol",1\r'
MIN_FUNCTONALITY = b'AT+CFUN=0\r'
NORMAL_FUNCTONALITY = b'AT+CFUN=1\r'
DISABLE_SLEEP = b'AT+QSCLK=0\r'
ENABLE_SLEEP = b'AT+QSCLK=1\r'
# ECHO_OFF = b'ATE0\r'
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
RI = 6
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

def reset_button_callback(ID,NUM):
	print("Reset button has been pressed")
	logging.info("Reset button has been pressed")
	strobe_light(0.2,4)

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
def check_float(false_detect_time = 5):
	# Check if the float swich is high for the false_detect_time
	temp_time = _time.perf_counter()
	while GPIO.input(FLOAT) == 0:
		if _time.perf_counter() - temp_time > false_detect_time:
			logging.info("The float was activated for %s seconds" % false_detect_time)
			strobe_light(0.5,4)

			return True
		_time.sleep(0.5)
	return False

def check_voltage(ina260):
	voltage = ina260.get_bus_voltage()
	current = ina260.get_current()

	print('V=%f,I=%f' % (voltage,current))
	logging.debug('V=%f,I=%f' % (voltage,current))

	return voltage, current

def receive_sms_callback(modem,ID):
	print("SMS Received")
	texts = modem.getSMS()
	print("Number of Texts Received: %d" % len(texts))
	for text in texts:
		if ID in text["message"]:
			print("ID Found")
			text["message"] = text["message"].lower()
			
			if "status" in text["message"]:
				print("Status Requested")
			elif "change id" in text["message"]:
				print("ID Change Requested")
			elif "change num" in text["message"]:
				print("Number Change Requested")
			else:
				print("Unknown Command? Request clarification from USER")
			# if "status" in text["message"]:
			# 	print("Status Requested")
			# if "status" in text["message"]:
			# 	print("Status Requested")	

def warmup():
	# Setup GPIO pins and define float/button pins
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(FLOAT, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
	GPIO.setup(DTR, GPIO.OUT, initial=GPIO.HIGH) # DTR pin on 4g module
	GPIO.setup(W_DISABLE, GPIO.OUT, initial=GPIO.LOW) # W_DISABLE pin on 4g module
	GPIO.setup(RI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # RI pin on 4g module
	GPIO.setup(PERST, GPIO.OUT, initial=GPIO.LOW) # PERST pin on 4g module
	GPIO.setup(STROBE, GPIO.OUT, initial=GPIO.LOW) # Strobe pin
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin

	GPIO.output(DTR,GPIO.LOW)
	_time.sleep(2)
	modem = smsModem()
	modem.connect()
	modem.signalTest()
	modem.refreshNetwork()
	modem.modeSelect("SMS")
	
	modem.ReadAll()
	modem_time = modem.requestTime()

	if modem_time != None:
		# Setup logging
		print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (modem_time.day,modem_time.month,modem_time.year,
			modem_time.hour,modem_time.minute,modem_time.second))
		try:
			logging.basicConfig(
				filename='logs/%s-%s-%s_%s-%s-%s.log' % (modem_time.day,modem_time.month,modem_time.year,
				modem_time.hour,modem_time.minute,modem_time.second), 
				filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG
				)
			logging.info('Log file has been created: logs/%s-%s-%s_%s-%s-%s.log' % (modem_time.day,modem_time.month,modem_time.year,
				modem_time.hour,modem_time.minute,modem_time.second))
		except:
			print("Log file could not be made")
	else:
		print("Modem was unable to sync time")
		try:
			logging.basicConfig(filename='logs/PI_CLK.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
		except:
			print("unable to create logfile using Pi's Clock")

	logging.info("Initialise and reset INA260 chip")
	ina260 = INA260(dev_address=0x40)
	ina260.reset_chip()
	_time.sleep(0.1)

	# Load settings from settings_.json
	ID, NUM = load_settings()

	GPIO.add_event_detect(BUTTON, GPIO.FALLING, 
            callback=lambda x: reset_button_callback(ID,NUM), bouncetime=3000)
	GPIO.add_event_detect(RI, GPIO.RISING,
            callback=lambda x: receive_sms_callback(modem,ID), bouncetime=1200)

	logging.info('Warmup has been completed')
	return ina260, modem

# MAIN gets called on script startup
def main():
	ina260,modem=warmup()

	

	while True:
		# GPIO.output(DTR,GPIO.LOW)
		# check water sensor
		if check_float() == True:
			print('Float switch is active')
			# send_txt('Float switch has been activated on module %s' % ID,NUM)

		temp_voltage, temp_current = check_voltage(ina260)
		if temp_voltage > 12.2:
			logging.warning("Voltage OKAY: %sV" % temp_voltage)
		elif temp_voltage <= 11.80:
			logging.warning("Voltage LOW: %sV" % temp_voltage)
		elif temp_voltage <= 11.60 :
			if warned == False:
				# send_txt("Module %s, Low Battery Warning: %sV" % (ID,temp_voltage),NUM)
				warned = True
			logging.warning("Voltage VERY LOW: %sV" % temp_voltage)

		# GPIO.output(DTR, GPIO.HIGH)
		
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
