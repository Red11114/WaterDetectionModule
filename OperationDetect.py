# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import required packages
import serial
import os, stat
import logging
from datetime import datetime
import json
import time as _time
import RPi.GPIO as GPIO
import threading

ID = ""
NUM = ""

# Define At command strings
OPERATE_SMS_MODE = 'AT+CMGF=1\r'
RECEIVE_SMS = 'AT+CMGL="REC UNREAD"\r'
CLEAR_READ = 'AT+CMGD=1,1'

# Message to report after water detection
MSG = 'The float switch has been activated'

# Serial settings
SERIAL_PORT = '/dev/ttyUSB2'
SERIAL_RATE = 115200

# Setup serial communication to the LTE modem
ser = serial.Serial(SERIAL_PORT,SERIAL_RATE)

# Setup GPIO pins and define float/button pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
GPIO.setup(22, GPIO.OUT, initial = GPIO.LOW) # Strobe pin

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

def warmup():
	# Setup logging
	datetime_object = datetime.now()
	print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second))
	try:
		logging.basicConfig(filename="logs/%s-%s-%s:%s-%s-%s_Operation.log" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second), filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
	except:
		print("Log file could not be made")
		logging.error("Log file could not be made")

	logging.info("Start warmup")
	# Load settings from settings_.json
	load_settings()
	# Add interurt events for the button 
	GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500)  
	GPIO.add_event_detect(27, GPIO.FALLING, callback=button_pressed, bouncetime=1500)
	strobe_light(0.1,2)
	if not ser.is_open:
		print("open serial")
		ser.open()
	sendCommand(OPERATE_SMS_MODE)
	sendCommand(CLEAR_READ)
	logging.info('Warmup has been completed')
	
# Function for sending AT commands
def sendCommand(command): 
	ser.write(command.encode())
	logging.info("Send command to LTE module %s" % command)
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
	logging.info("Attempt to receive text")
	# Open serial if required
	if not ser.is_open:
		logging.info("Open serial")
		ser.open()
	# Read in the modems first response
	reply = ser.read(ser.in_waiting)
	print(reply)
	# Check for a serial response
	if reply != "":
		print("serial data received, try to receive SMS")
		logging.info("serial data received, try to receive SMS")
		sendCommand(RECEIVE_SMS)
		reply = ser.read(ser.in_waiting).decode()
		print("RECEIVE_SMS Response: %s" % reply)
		# Check if the reply contains a received SMS
		if reply.find("CMGL: ") != -1:
			# Split the reply inot individual responses
			reply_lines = reply.split("\n")
			print("reply_lines %s" % reply_lines)
			# Create info list of received SMS response
			for i in range(len(reply_lines)):
				if reply_lines[i].find("CMGL: ") != -1:
					response_index = i
					print("response at index: %s"% i)
			info_list = reply_lines[response_index]
			info_list = info_list.split(",")
			print("info_list: %s" % info_list)
			# Find number of txts in mem, the sender's number and the text msg
			txt_num = info_list[0]
			txt_num = txt_num[len(txt_num)-1:len(txt_num)]
			print("NUMBER OF TXTS: %s" % txt_num)
			number = info_list[2]
			number = number[1:len(number)-1]
			print("NUMBER: %s" % number)
			text_msg = reply_lines[response_index+1]
			print("TEXT: %s" % text_msg)
			# Clear the modems SMS memory
			sendCommand(CLEAR_READ)
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
					return True
				elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
					confirming = False
					return False
				else:
					send_txt('Confirmation spelt incorrectly',txt_number)
					logging.warning("error: confirmation not correctly spelt")
			else:
				send_txt('Reply in format: ID yes/no, Example: 0005 yes',txt_number)
		_time.sleep(2)
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

# Function called when float switch detects water
# Alerts the user by SMS and waits for a response
def float_pressed(channel):
	global ID
	global NUM
	# initialise active check time
	check = False
	check_time = _time.perf_counter()
	false_detect_time = 30
	# Check if the float swich is high for the false_detect_time
	while GPIO.input(17) == 0 and check == False:
		if _time.perf_counter() - check_time > false_detect_time:
			check = True
			break
		_time.sleep(1)
	# The float switch is considered active
	if check == True:
		send_txt('Float switch has been activated: Please confirm water present at the end of the bay, Reply yes/no within 30 minutes',NUM)
		confirmation = receive_confirmation(30*60)
		if confirmation == True:
			send_txt('Water Confirmed: float set to inactive, reset when ready',NUM)
			try:
				GPIO.remove_event_detect(17)
				logging.info("Event detect disabled for float switch")
			except:
				logging.warning("Event detect could not be disabled for float switch")
				pass
		elif confirmation == False:
			send_txt('Continuing detection',NUM)
		elif confirmation == None:
			send_txt('Timer ran out: continuing detection',NUM)

# Fucntion called when button is pressed
# Used to reset the water sensor between bays
def button_pressed(channel):
	global NUM
	logging.info("The button has been Activated")
	# initialise active check time
	check = False
	check_time = _time.perf_counter()
	false_detect_time = 4
	# Check if the float swich is high for the false_detect_time
	while GPIO.input(27) == 0 and check == False:
		if _time.perf_counter() - check_time > false_detect_time:
			logging.info("The button was held for 4 seconds")
			check = True
		_time.sleep(1)
	# The button is considered pressed
	if check == True:
		send_txt('Button has been pressed. Do you wish to reset the Float switch? Reply yes/no within 2 minutes',NUM)
		# Start a confirmation receive for x seconds
		confirmation = receive_confirmation(60*2)
		if confirmation == True:
			print("Resetting the float switch detection")
			try:
				GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500) 
				logging.info("Event detect enabled for float switch")
				send_txt('Float switch has been activated',NUM)
			except:
				logging.warning("Event detect could not be enabled for float switch")
				pass
		elif confirmation == False:
			send_txt('Reset Declined',NUM)
		elif confirmation == None:
			send_txt('Timer ran out',NUM)

# MAIN gets called on script startup
def main():
	global ID
	global NUM
	global confirming
	
	warmup()
	# Enter loop for receiving SMS's
	confirming = False
	while True:
		if confirming == False:
			print("Waiting for SMS")
			# check if there has been a text received
			txt_number, txt_msg = receive_txt()
			if txt_msg != None:
				logging.info("Text received")
				# make sure the text include the modules ID
				if txt_msg.find(ID) != -1:
					logging.info("Text has correct ID for module")
					# check if the text includes "change"
					if txt_msg.find("change") != -1 or txt_msg.find("Change") != -1:
						logging.info("Change number requested")
						# Find the number after the "#"
						if txt_msg.find("#") != -1:
							new_num = txt_msg.split("#")
							new_num = new_num[len(new_num)-1]
							new_num = new_num[0:12]
							print("Number :%s" % new_num)
							# Check if the format of the number is correct
							if len(new_num) == len(NUM) and new_num.find('+614') != -1: 
								send_txt('Setting main number to %s\nconfirm yes/no within 1 minute' % new_num, txt_number)
								# Start a confirmation receive for x seconds
								confirmation = receive_confirmation(60)
								if confirmation == True:
									send_txt('Number Change Accepted, new number: %s' % new_num, txt_number)
									NUM = new_num
									write_settings()
									print("New Number set to %s" % NUM)
								elif confirmation == False:
									send_txt('Number Change Declined', txt_number)
								elif confirmation == None:
									send_txt('Timer ran out', txt_number)
							else:
								send_txt('The number specified does not meet the required format: +614xxxxxxxx', txt_number)
						else:
							send_txt('For a number change request please use the following format: ID change #number, Example: 0005 change #+61457242753', txt_number)
					else:
						print("Correct ID received but command not recognised")
						logging.warning("Correct ID received but command not recognised")
		_time.sleep(2)

if __name__ == "__main__":
	try:
		main()
	except ValueError as e:
		logging.info("Error : {}".format(e))
