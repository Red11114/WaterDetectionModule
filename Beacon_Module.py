#!/bin/bash
# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import builtin packages
import os
import logging
from datetime import datetime, date
import json
import time
import subprocess
import sys

# Import installed packages
import RPi.GPIO as GPIO

# Import drivers
from INA260_MINIMAL import INA260
from EC25_Driver import smsModem

# Pi Zero Pin definitions
## hardware
FLOAT = 17
BUTTON = 27
LED = 22
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

def LED_light(secconds, count):
	logging.info("LED light :)")
	i = 0
	while i < count:
		GPIO.output(LED, GPIO.HIGH)
		time.sleep(secconds/2)
		GPIO.output(LED, GPIO.LOW)
		time.sleep(secconds/2)
		i +=1

def check_float(false_detect_time = 5):
	# Check if the float swich is high for the false_detect_time
	temp_time = time.perf_counter()
	while GPIO.input(FLOAT) == 0:
		if time.perf_counter() - temp_time > false_detect_time:
			logging.info("The float was activated for %s seconds" % false_detect_time)
			LED_light(0.5,4)

			return "Water Present"
		time.sleep(0.5)
	print("Float not active")
	return "No Water"

def check_voltage(ina260):
	voltage = ina260.get_bus_voltage()
	current = ina260.get_current()

	print('V=%6.4f,I=%6.4f,' % (voltage,current))
	logging.debug('V=%6.4f,I=%6.4f,' % (voltage,current))

	return voltage, current

def check_wifi_status():
	cmd = 'cat /sys/class/net/wlan0/operstate'
	response = subprocess.check_output(cmd,shell=True)[:-1]
	print("wifi check response = %s" % response)
	return response

def turn_wifi_on():
    cmd = 'sudo /home/pi/waterdetectionmodule/wifi_on.sh'
    response = os.system(cmd)
    return response

def turn_wifi_off():
    cmd = 'sudo /home/pi/waterdetectionmodule/wifi_off.sh'
    response = os.system(cmd)
    return response

def button_callback(ID,NUM):
	global button_active

	if button_active == "True":
		button_active = "False"
	elif button_active == "False":
		button_active = "True"

def receive_sms_callback(ina260,modem,ID,NUM):
	global button_active
	global sms_flag
	global voltage_flag
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
				LED_light(0.2,5)
				logging.info("ID Found")
				print("ID Found")
				print(text)
				if "start" in text["message"]:
					logging.info("Start Requested")
					print("Start Requested")
					# Reset SMS sending loop
					sms_flag = 0

					voltage,current = check_voltage(ina260)
					float_status = check_float(2)

					modem.sendMessage(recipient=text["number"].encode(),message=b'Module %s Has Begun Detecting For Water, Current Status=%s, Voltage=%4.2f' % 
									(ID.encode(),float_status.encode(),voltage)
									)
				elif "debug" in text["message"]:
					logging.info("Debug Requested")
					print("Debug Requested")
					voltage,current = check_voltage(ina260)
					float_status = check_float(2)
					signal_conn = modem.signalTest()
					wifi_status = check_wifi_status()

					modem.sendMessage(recipient=text["number"].encode(),message=b'Status Response From Module %s: Water Detected=%s, Voltage=%4.2f, Current=%4.2f, Signal=%b/100, WiFi=%s, SMS Flag=%d, Voltage Flag=%d, Button Active=%s' % 
									(ID.encode(),float_status.encode(),voltage,current*1000,signal_conn,wifi_status,sms_flag,voltage_flag,button_active)
									)
				elif "status" in text["message"]:
					logging.info("Status Requested")
					print("Status Requested")
					voltage,current = check_voltage(ina260)
					float_status = check_float(2)
					signal_conn = modem.signalTest()
					wifi_status = check_wifi_status()

					modem.sendMessage(recipient=text["number"].encode(),message=b'Status Response From Module %s: Water Detected=%s, Voltage=%4.2f, Current=%4.2f, Signal=%b/100, WiFi=%s' % 
									(ID.encode(),float_status.encode(),voltage,current*1000,signal_conn,wifi_status)
									)
				elif "stop" in text["message"]:
					logging.info("Stop Requested")
					print("Stop Requested")
					# Stop SMS sending loop
					sms_flag = 10

					voltage,current = check_voltage(ina260)
					float_status = check_float(2)

					modem.sendMessage(recipient=text["number"].encode(),message=b'Module %s Has Stopped Detecting Water, Current Status=%s, Voltage=%4.2f' % 
									(ID.encode(),float_status.encode(),voltage)
									)
				elif "credentials" in text["message"]:
					if button_active == True:
						ID,NUM = load_settings()
						print("send back settings")
						modem.sendMessage(recipient=text["number"].encode(),message=b'Credentials Response From Module %s Nummber=%s' % 
									(ID.encode(),NUM)
									)
					else:
						logging.info("not in config mode")
						print("not in config mode")
				elif "changeid" in text["message"]:
					if button_active == True:
						print("ID Change Requested")
						for i in range(len(text["message"])):		# loop through split message for the index of changeid
							if "changeid" in text["message"][i]:		# New id should follow changeid 
								new_id = text["message"][i+1]
								if len(new_id) == len(ID) and new_id != ID and new_id.isdigit() == True:	# check if ID is acceptable
									print("ID is %s" % new_id)
									logging.info("ID is %s" % new_id)
									modem.sendMessage(recipient=text["number"].encode(),message=b'Credentials Set For Module %s New ID=%s' % 
									(ID.encode(),new_id)
									)
									ID = new_id
									write_settings(ID,NUM)
								else:
									print("ID does not match requirements")
									modem.sendMessage(recipient=text["number"].encode(),message=b'Credentials Denied For Module %s New ID=%s is invalid' % 
									(ID.encode(),new_id)
									)
					else:
						logging.info("not in config mode")
						print("not in config mode")
				elif "changenum" in text["message"]:
					if button_active == True:
						print("Number Change Requested")
						for i in range(len(text["message"])):		# loop through split message for the index of changeid
							if "changenum" in text["message"][i]:		# New id should follow changeid 
								new_num = text["message"][i+1]
								if "+614" in new_num and len(new_num) == 12 and new_num[1:].isdigit() == True:
									print("NUM is %s" % new_num)
									logging.info("NUM is %s" % new_num)
									modem.sendMessage(recipient=text["number"].encode(),message=b'Credentials Set For Module %s New Number=%s' % 
									(ID.encode(),new_num)
									)
									NUM = new_num
									write_settings(ID,NUM)
								elif "04" in new_num and len(new_num) == 10 and new_num.isdigit() == True:	# check if ID is acceptable
									print("NUM is %s" % new_num)
									NUM = "+61" + new_num[1:]
									print(NUM)
									write_settings(ID,NUM)
								else:
									print("NUmber does not match requirements")
									modem.sendMessage(recipient=text["number"].encode(),message=b'Credentials Denied For Module %s New Number=%s is invalid' % 
									(ID.encode(),new_id)
									)
					else:
						logging.info("not in config mode")
						print("not in config mode")
						LED_light(1,2)
				elif "wifi on" in text["message"]:
					if button_active == True:
						logging.info("wifi on Requested")
						print("wifi on Requested")
						wifi_status = check_wifi_status().decode()
						if 'up' in wifi_status:
							print("wifi already on")
							logging.info("wifi already on")
							modem.sendMessage(recipient=text["number"].encode(),message=b'Wifi is already on')
						if 'down' in wifi_status:
							print("turning wifi on")
							logging.info("turning wifi on")
							turn_wifi_on()
							wifi_status = check_wifi_status().decode()
							while "up" not in wifi_status:
								print("waiting for wifi to turn on")
								wifi_status = check_wifi_status().decode()
								time.sleep(1)
							wifi_status = check_wifi_status()
							modem.sendMessage(recipient=text["number"].encode(),message=b'Wifi has been set to %s' % wifi_status)
					else:
						logging.info("not in config mode")
						print("not in config mode")
				elif "wifi off" in text["message"]:
					if button_active == True:
						logging.info("wifi off Requested")
						print("wifi off Requested")
						wifi_status = check_wifi_status().decode()
						if 'down' in wifi_status:
							print("wifi already off")
							logging.info("wifi already off")
							modem.sendMessage(recipient=text["number"].encode(),message=b'Wifi is already off')
						if 'up' in wifi_status:
							print("turning wifi off")
							logging.info("turning wifi off")
							turn_wifi_off()
							wifi_status = check_wifi_status()
							modem.sendMessage(recipient=text["number"].encode(),message=b'Wifi has been set to %s' % wifi_status)
					else:
						logging.info("not in config mode")
						print("not in config mode")
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
	GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW) # LED pin
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin

	# time.sleep(10)
	time.sleep(2)
	GPIO.output(PERST, GPIO.HIGH)
	time.sleep(0.5)
	GPIO.output(PERST, GPIO.LOW)
	time.sleep(1)
	GPIO.output(DTR, GPIO.LOW)
	time.sleep(1)

	modem = smsModem()
	modem.connect()
	modem.config()
	modem.clearMessage("ALL")
	time.sleep(1)
	modem.signalTest()

	modem_time = modem.requestTime()
	modem.disconnect()
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
            callback=lambda x: button_callback(ID,NUM), bouncetime=3000)
	GPIO.add_event_detect(RI, GPIO.RISING,
            callback=lambda x: receive_sms_callback(ina260,modem,ID,NUM), bouncetime=200)

	logging.info('Warmup has been completed')
	LED_light(0.5,4)
	return ina260, modem, ID, NUM

# MAIN gets called on script startup
def main():
	global sms_flag
	global voltage_flag
	global button_active
	
	sms_flag = 0
	voltage_flag = 0
	button_active =  False
	
	ina260,modem,ID,NUM=warmup()

	while True:
		if check_float() == True and sms_flag <= 1:
			voltage,current = check_voltage(ina260)
			# check water sensor
			print('Float switch is active')
			logging.info('Float switch is active')

			# wake up module
			GPIO.output(DTR,GPIO.LOW)
			time.sleep(0.2)
			modem.connect()
			modem.sendMessage(recipient=NUM.encode(),message=b'Module %s Has Detected Water! Voltage=%4.2f' % 
									(ID.encode(),voltage)
									)
			# set module into sleep again
			GPIO.output(DTR, GPIO.HIGH)

			sms_flag += 1
			print("Flag State: %d" % sms_flag)
			logging.info("Flag State: %d" % sms_flag)
		else:
			voltage,current = check_voltage(ina260)
			# check water sensor
			if (voltage >= 12.5) and (voltage_flag >=0):
				logging.warning("Voltage GOOD: %sV" % voltage)
				print("send text for GOOD")
				# wake up module
				GPIO.output(DTR,GPIO.LOW)
				time.sleep(0.2)
				modem.connect()
				modem.sendMessage(recipient=NUM.encode(),message=b'Module %s Battery Charge OK! Voltage=%4.2f' % 
										(ID.encode(),voltage)
										)
				voltage_flag = -1
			if (11.6 > voltage >= 11.4) and (voltage_flag < 1):
				logging.warning("Voltage LOW: %sV" % voltage)
				print("send text for LOW")
				# wake up module
				GPIO.output(DTR,GPIO.LOW)
				time.sleep(0.2)
				modem.connect()
				modem.sendMessage(recipient=NUM.encode(),message=b'Module %s LOW VOLTAGE WARNING! Voltage=%4.2f Direct solar panel towards most consistent sunlight' % 
										(ID.encode(),voltage)
										)
				voltage_flag = 1
			elif (11.4 > voltage) and (voltage_flag <= 1):
				logging.warning("Voltage VERY LOW: %sV" % voltage)
				print("send text for VERY LOW")
				# wake up module
				GPIO.output(DTR,GPIO.LOW)
				time.sleep(0.2)
				modem.connect()
				modem.sendMessage(recipient=NUM.encode(),message=b'Module %s VERY LOW VOLTAGE WARNING!! Voltage=%4.2f Module may run out of power, consider recharging the battery' % 
										(ID.encode(),voltage)
										)
				voltage_flag = 2
			else:
				logging.warning("Voltage UNKNOWN: %sV" % voltage)
				print("unknown voltage")

		wait_time = 30
		temp_time = time.perf_counter()
		while button_active == False and (time.perf_counter() - temp_time > wait_time*60):
			time.sleep(60)
		LED_light(1,2)

if __name__ == "__main__":
	try:
		main()
	except ValueError as e:
		logging.info("Error : {}".format(e))
