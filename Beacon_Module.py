#!/bin/bash
# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import builtin packages
import os
import logging
from datetime import datetime, date
import json
import time

# Import installed packages
import RPi.GPIO as GPIO

# Import drivers
from INA260_MINIMAL import INA260
from EC25_Driver import smsModem

# Pi Zero Pin definitions
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
		ID = str(s['ID'])
		NUM = str(s['NUM'])
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
		'ID': str(ID),
		'NUM': str(NUM)
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
		# GPIO.output(STROBE, GPIO.HIGH)
		time.sleep(0.5)
		# GPIO.output(STROBE, GPIO.LOW)
		time.sleep(secconds)
		i +=1

# Alerts the user by SMS
def check_float(false_detect_time = 5):
	# Check if the float swich is high for the false_detect_time
	temp_time = time.perf_counter()
	while GPIO.input(FLOAT) == 0:
		if time.perf_counter() - temp_time > false_detect_time:
			logging.info("The float was activated for %s seconds" % false_detect_time)
			strobe_light(0.5,4)

			return True
		time.sleep(0.5)
	print("Float not active")
	return False

def check_voltage(ina260):
	voltage = ina260.get_bus_voltage()
	current = ina260.get_current()

	print('V=%f,I=%f' % (voltage,current))
	logging.debug('V=%f,I=%f' % (voltage,current))

	return voltage, current

def check_wifi_status():
	cmd = 'cat /sys/class/net/wlan0/operstate'
	response = os.system(cmd)
	print(response)
	if response == 0:
		response = "up"
	elif response == 1:
		response = "down"
	print(response)
	return response

def turn_wifi_on():
    cmd = 'sudo /home/pi/waterdetectionmodule/wifi_on.sh'
    response = os.system(cmd)
    return response

def turn_wifi_off():
    cmd = 'sudo /home/pi/waterdetectionmodule/wifi_off.sh'
    response = os.system(cmd)
    return response


def receive_sms_callback(ina260,modem,ID,NUM):
	logging.info("SMS Received")
	print("SMS Received")
	GPIO.output(DTR,GPIO.LOW)
	time.sleep(0.2)
	modem.connect()
	texts = modem.getSMS()
	
	if texts != None:
		logging.info("Number of Texts Received: %d" % len(texts))
		print("Number of Texts Received: %d" % len(texts))
		for text in texts:
			if ID in text["message"]:
				strobe_light(0.2,5)
				logging.info("ID Found")
				print("ID Found")
				# text["message"] = text["message"].lower().split(' ')
				print(text)
				if "status" in text["message"]:
					logging.info("Status Requested")
					print("Status Requested")
					voltage,current = check_voltage(ina260)
					float_status = check_float(10)
					if float_status == True:
						float_status = "True"
					else:
						float_status = "False"
					signal_conn = modem.signalTest()
					wifi_status = check_wifi_status()

					modem.sendMessage(recipient=text["number"].encode(),message=b'Status Response From Module %s:\rWater Detected=%s, Voltage=%4.2f, Current=%4.2f\r, Signal=%b/100, WiFi=%s' % 
									(ID.encode(),float_status.encode(),voltage,current*1000,signal_conn,wifi_status.encode())
									)

				elif "credentials" in text["message"]:
					print("send back settings")
				elif "changeid" in text["message"]:
					print("ID Change Requested")
					for i in range(len(text["message"])):		# loop through split message for the index of changeid
						if "changeid" in text["message"][i]:		# New id should follow changeid 
							new_id = text["message"][i+1]
							if len(new_id) == len(ID) and new_id != ID and new_id.isdigit() == True:	# check if ID is acceptable
								print("ID is %s" % new_id)
								ID = new_id
								# write_settings(ID,NUM)
							else:
								print("ID does not match requirements")

				elif "changenum" in text["message"]:
					print("Number Change Requested")
					for i in range(len(text["message"])):		# loop through split message for the index of changeid
						if "changenum" in text["message"][i]:		# New id should follow changeid 
							new_num = text["message"][i+1]
							if "+614" in new_num and len(new_num) == 12 and new_num[1:].isdigit() == True:
								print("NUM is %s" % new_num)
								NUM = new_num
								# write_settings(ID,NUM)
							elif "04" in new_num and len(new_num) == 10 and new_num.isdigit() == True:	# check if ID is acceptable
								print("NUM is %s" % new_num)
								NUM = "+61" + new_num[1:]
								print(NUM)
								# write_settings(ID,NUM)
							else:
								print("ID does not match requirements")
				elif "wifi on" in text["message"]:
					logging.info("wifi on Requested")
					print("wifi on Requested")
					wifi_status = check_wifi_status()
					print("wifi_status: %s" % wifi_status)
					turn_wifi_on()

				elif "wifi off" in text["message"]:
					logging.info("wifi off Requested")
					print("wifi off Requested")
					wifi_status = check_wifi_status()
					turn_wifi_off()
				else:
					print("Unknown Command? Request clarification from USER")
					
	print("going into sleep mode")
	GPIO.output(DTR,GPIO.HIGH)

def warmup():
	# Setup GPIO pins and define float/button pins
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(FLOAT, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
	GPIO.setup(DTR, GPIO.OUT, initial=GPIO.LOW) # DTR pin on 4g module
	GPIO.setup(W_DISABLE, GPIO.OUT, initial=GPIO.LOW) # W_DISABLE pin on 4g module
	GPIO.setup(RI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # RI pin on 4g module
	GPIO.setup(PERST, GPIO.OUT, initial=GPIO.LOW) # PERST pin on 4g module
	GPIO.setup(STROBE, GPIO.OUT, initial=GPIO.LOW) # Strobe pin
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
	time.sleep(0.5)
	GPIO.output(PERST, GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(PERST, GPIO.LOW)
	time.sleep(1)
	GPIO.output(DTR, GPIO.LOW)
	time.sleep(1)

	# modem = smsModem()
	# active = modem.ReadAll()
	# while "RDY" not in active:
	# 	print("waiting")
	# 	active = modem.ReadAll()
		

	modem = smsModem()
	modem.connect()
	modem.config()
	modem.clearMessage("ALL")
	modem.signalTest()
	
	print("left in  buffer: %s"% modem.ReadAll())

	modem_time = modem.requestTime()

	print("entering Sleep")
	GPIO.output(DTR, GPIO.HIGH)

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
	time.sleep(0.1)

	# Load settings from settings_.json
	ID, NUM = load_settings()

	GPIO.add_event_detect(BUTTON, GPIO.FALLING, 
            callback=lambda x: reset_button_callback(ID,NUM), bouncetime=3000)
	GPIO.add_event_detect(RI, GPIO.RISING,
            callback=lambda x: receive_sms_callback(ina260,modem,ID,NUM), bouncetime=200)

	# strobe_light(1,2)

	logging.info('Warmup has been completed')
	return ina260, modem, ID, NUM

# MAIN gets called on script startup
def main():
	check_wifi_status()
	turn_wifi_on() 
	check_wifi_status()
	ina260,modem,ID,NUM=warmup()

	sms_flag = 0
	voltage_flag = 0

	while True:
		# check water sensor
		if check_float() == True and sms_flag < 2:
			print('Float switch is active')
			logging.info('Float switch is active')
			# strobe_light(2,2)

			# wake up module
			GPIO.output(DTR,GPIO.LOW)
			time.sleep(0.2)
			modem.connect()
			modem.sendMessage(recipient=NUM.encode(),message=b'Float switch has been activated on module %s' % ID.encode())

			# set module into sleep again
			GPIO.output(DTR, GPIO.HIGH)

			sms_flag += 1
			print("Flag State: %d" % sms_flag)
		time.sleep(1)

		temp_voltage, temp_current = check_voltage(ina260)

		if temp_voltage >= 13:
			logging.warning("Voltage CHARGING: %sV" % temp_voltage)
			print("send text for CHARGING")
			strobe_light(0.5,4)
		elif 13 > temp_voltage >= 11.8:
			logging.warning("Voltage GOOD: %sV" % temp_voltage)
			print("send text for GOOD")
		elif 11.8 > temp_voltage >= 11.4:
			logging.warning("Voltage LOW: %sV" % temp_voltage)
			print("send text for LOW")
		elif 11.4 > temp_voltage:
			logging.warning("Voltage VERY LOW: %sV" % temp_voltage)
			print("send text for VERY LOW")
		else:
			print("unknown voltage")

		time.sleep(30*60)

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
