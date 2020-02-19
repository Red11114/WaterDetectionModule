#! /usr/bin/python3

# This script sends SMS from Sixfab GSM/SPRS shield, 3G,4G/LTE Base Shield v2, RPi Cellular IoT App. Shield
# for running it: python3 sendSMS_python3.py <serial0/ttyUSB0/> <'NUMBER'> <"Your Message">
# Example: python3 sendSMS_python3 serial0 '+0123456789' "This is sample message" 

import serial
import time as _time
# from gpiozero import Button
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

global NUM = '+61448182742'
MSG = 'The float switch has been activated'

SERIAL_PORT = '/dev/ttyUSB2'
SERIAL_RATE = 115200
ser = serial.Serial(SERIAL_PORT,SERIAL_RATE)

OPERATE_SMS_MODE = 'AT+CMGF=1\r'
SEND_SMS = 'AT+CMGS="%s"\r'% NUM
RECEIVE_SMS = 'AT+CMGL="REC UNREAD'

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin

def sendCommand(command): 
	ser.write(command.encode())
	_time.sleep(0.2)
	
def float_pressed(channel):
	check = False
	check_time = _time.perf_counter()
	while GPIO.input(17) == 0:
		if _time.perf_counter() - check_time > 3:
			check = True
			break
	if check == True:
		send_txt('Float switch has been activated: Please confirm water present at the end of the bay, Reply yes/no within 5 minutes')
		time = _time.perf_counter()
		while _time.perf_counter() < time + 300:
			print("Countdown: %d "% (300 - (_time.perf_counter() - time)))
			number, txt_msg = receive_txt()
			_time.sleep(0.2)
			print("number %s NUM %s" % (number,NUM))
			if number == NUM:
				print("Received confirmation reply: %s" % txt_msg)
				if (txt_msg.find("yes") != -1) or (txt_msg.find("Yes") != -1):
					send_txt('Water Confirmed: float set to inactive, reset when ready')
					try:
						GPIO.remove_event_detect(17)
					except:
						pass

					break
				elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
					send_txt('Continuing detection')
					break
				else:
					print("error: confirmation not correctly spelt")
			else:
				print("txt sent by wrong number")
			_time.sleep(1.8)
		print("TIMER OUT")
	
def button_pressed(channel):
	check = False
	check_time = _time.perf_counter()
	while GPIO.input(27) == 0:
		if _time.perf_counter() - check_time > 2:
			check = True
		
	if check == True:
		print("Button: Reseting on a new bay")
		send_txt('Button has been pressed. Do you wish to reset the Float switch? Reply yes/no within 2 minutes')
		
		comfirmation = receive_confirmation(60)
		if comfirmation == True:
			print("Resetting the float switch detection")
			try:
				GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500)  
			except:
				pass
		elif comfirmation == False:
			send_txt('Reset Declined')
		elif comfirmation == None:
			send_txt('Timer ran out')

def send_txt(message):
	print ("Sending SMS to %s"% NUM)
	if not ser.is_open:
		print("open serial")
		ser.open()
	if ser.is_open:
		print("serial is open")
		print("SMS SENT: %s" % message)
		# sendCommand(OPERATE_SMS_MODE)
		# sendCommand(SEND_SMS)
		# sendCommand(message)
		# sendCommand('\x1A')	#sending CTRL-Z
		ser.close()
		print("close serial")

def receive_txt():
	if not ser.is_open:
		print("open serial")
		ser.open()
	reply = ser.read(ser.in_waiting)
	if reply != "":
		sendCommand('AT+CMGL="REC UNREAD"\r')
		reply = ser.read(ser.in_waiting).decode()
		msg_check = reply.find("CMGL: ")
		if msg_check != -1:
			reply_lines = reply.split("\n")
			# print("reply_lines %s" % reply_lines)

			info_list = reply_lines[1]
			# print("info_list: %s" % info_list)

			number = info_list.split(",")
			number = number[2]
			number = number.split('"')
			number = number[1]
			print("NUMBER: %s" % number)

			text_msg = reply_lines[2]
			print("TEXT: %s" % text_msg)
			return number, text_msg
		else:
			return None,None
	
def receive_confirmation(timer):
	print("Starting timer for %s seconds" % timer)
	time = _time.perf_counter()
	while _time.perf_counter() < time + timer:
		print("Countdown: %d"% (timer - (_time.perf_counter() - time)))
		number, txt_msg = receive_txt()
		_time.sleep(0.2)
		if number == NUM:
			print("Received confirmation reply: %s" % txt_msg)
			if (txt_msg.find("yes") != -1) or (txt_msg.find("Yes") != -1):
				return True
			elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
				return False
			else:
				print("error: confirmation not correctly spelt")
		else:
			print("waiting for coinfirmation...")
		_time.sleep(1.8)
	print("TIMER OUT")
	return None

def main():
	global NUM
	if not ser.is_open:
		print("open serial")
		ser.open()

	GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500)  
	GPIO.add_event_detect(27, GPIO.FALLING, callback=button_pressed, bouncetime=1500)

	sendCommand("AT+CMGF=1\r")
	sendCommand('AT+CMGD=4\r')
	
	while True:
		number, text = receive_txt()
		if text != None:
			if text.find("change") != -1 or text.find("Change") != -1:
				new_num = text.split("#")
				new_num = new_num[len(new_num)-1]
				send_txt('Setting main number to %s\nconfirm yes/no within 1 minute' % new_num)
				
				comfirmation = receive_confirmation(60)
				if comfirmation == True:
					send_txt('Number Change Accepted, new number: %s' % new_num)
					NUM = new_num
				elif comfirmation == False:
					send_txt('Number Change Declined')
				elif comfirmation == None:
					send_txt('Timer ran out')

		_time.sleep(5)
			
	
	# sendCommand('AT\r')
	# num = ser.in_waiting
	# print(num)
	# while num > 0:
	# 	print(ser.readline().decode())
	# 	sleep(0.1)
	# 	num = ser.in_waiting
	# 	print(num)
	# ser.close()
	# sleep(1)
	
	# ser.open()
	# sendCommand('AT+CPMS="SM","SM","SM"')
	# num = ser.in_waiting
	# print(num)
	# while num > 0:
	# 	print(ser.readline().decode())
	# 	sleep(0.1)
	# 	num = ser.in_waiting
	# 	print(num)
	# ser.close()
	# sleep(1)

	# while True:
	# 	response = ser.readline()
	# 	print(response.decode())
	# 	if 'OK' in response.decode():
	# 		print("got an OK")
	# 		break
	# print("Started detecting for water")
	
	# response = ""
	# while True:
	# 	if not ser.is_open:
	# 		print("open serial")
	# 		ser.open()
	# 	if ser.is_open:
	# 		print("serial is open")
	# 		print("checking for sms")
	# 		# sendCommand('AT+CPMS?')
	# 		sendCommand('AT+CMGF=1\r')
	# 		while True:
				
	# 			sendCommand('AT+CMGR="18"')
	# 			sleep(0.1)
	# 			response = ser.readline()
	# 			print(response.decode())
	# 	sleep(1)

if __name__ == "__main__":
	try:
		main()
	except ValueError as e:
		print ("Error : {}".format(e))
