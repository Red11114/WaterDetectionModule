# A script that listens for SMS's with commands and replys accordingly
# will detect water and alert the user via the number saved

# Import required packages
import serial
import time as _time
import RPi.GPIO as GPIO
import threading

# Import configuration files
import settings_ as SE

# Setup serial communication to the LTE modem
ser = serial.Serial(SE.SERIAL_PORT,SE.SERIAL_RATE)

# Setup GPIO pins and define float/button pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
GPIO.setup(22, GPIO.OUT, initial = GPIO.LOW) # Strobe pin

# class Led(object):

#     LED_OFF = 0
#     LED_ON = 1
#     LED_FLASHING = 2

#     # the short time sleep to use when the led is on or off to ensure the led responds quickly to changes to blinking
#     FAST_CYCLE = 0.05

#     def __init__(self, led_pin):
#         # create the semaphore used to make thread exit
#         self.pin_stop = threading.Event()
#         # the pin for the LED
#         self.__led_pin = led_pin
#         # initialise the pin and turn the led off
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(self.__led_pin, GPIO.OUT)
#         # the mode for the led - off/on/flashing
#         self.__ledmode = Led.LED_OFF
#         # make sure the LED is off (this also initialises the times for the thread)
#         self.off()
#         # create the thread, keep a reference to it for when we need to exit
#         self.__thread = threading.Thread(name='ledblink',target=self.__blink_pin)
#         # start the thread
#         self.__thread.start()

#     def blink(self, time_on=0.050, time_off=1):
#         # blinking will start at the next first period
#         # because turning the led on now might look funny because we don't know
#         # when the next first period will start - the blink routine does all the
#         # timing so that will 'just work'
#         self.__ledmode = Led.LED_FLASHING
#         self.__time_on = time_on
#         self.__time_off = time_off

#     def off(self):
#         self.__ledmode = self.LED_OFF
#         # set the cycle times short so changes to ledmode are picked up quickly
#         self.__time_on = Led.FAST_CYCLE
#         self.__time_off = Led.FAST_CYCLE
#         # could turn the LED off immediately, might make for a short flicker on if was blinking

#     def on(self):
#         self.__ledmode = self.LED_ON
#         # set the cycle times short so changes to ledmode are picked up quickly
#         self.__time_on = Led.FAST_CYCLE
#         self.__time_off = Led.FAST_CYCLE
#         # could turn the LED on immediately, might make for a short flicker off if was blinking

#     def reset(self):
#         # set the semaphore so the thread will exit after sleep has completed
#         self.pin_stop.set()
#         # wait for the thread to exit
#         self.__thread.join()
#         # now clean up the GPIO
#         GPIO.cleanup()

def warmup():
	# Add interurt events for the button 
	GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500)  
	GPIO.add_event_detect(27, GPIO.FALLING, callback=button_pressed, bouncetime=1500)

	# Initialise LED blinking thread
	t = threading.Thread(target=strobe_light, args=(1,))
	t.start()

	if not ser.is_open:
		print("open serial")
		ser.open()
	sendCommand(SE.OPERATE_SMS_MODE)
	sendCommand(SE.CLEAR_READ)
	
# Function for sending AT commands
def sendCommand(command): 
	ser.write(command.encode())
	_time.sleep(0.2)

# Function for sending a Text
def send_txt(message):
	print ("Sending SMS to %s"% SE.NUM)
	if not ser.is_open:
		print("open serial")
		ser.open()
	if ser.is_open:
		print("serial is open")
		print("SMS SENT: %s" % message)
		# sendCommand(SE.OPERATE_SMS_MODE)
		# sendCommand(SE.SEND_SMS)
		# sendCommand(message)
		# sendCommand('\x1A')	#sending CTRL-Z
		ser.close()
		print("close serial")

# Function for receiving a Text. 
# will respond accordingly?
def receive_txt():
	if not ser.is_open:
		print("open serial")
		ser.open()
	reply = ser.read(ser.in_waiting)
	if reply != "":
		sendCommand(SE.RECEIVE_SMS)
		reply = ser.read(ser.in_waiting).decode()
		msg_check = reply.find("CMGL: ")
		if msg_check != -1:
			reply_lines = reply.split("\n")
			print("reply_lines %s" % reply_lines)

			info_list = reply_lines[1]
			info_list = info_list.split(",")
			print("info_list: %s" % info_list)

			txt_num = info_list[0]
			txt_num = txt_num[len(txt_num)-1:len(txt_num)]
			print("NUMBER OF TXTS: %s" % txt_num)

			number = info_list[2]
			number = number[1:len(number)-1]
			print("NUMBER: %s" % number)

			text_msg = reply_lines[2]
			print("TEXT: %s" % text_msg)

			sendCommand(SE.CLEAR_READ)
			return number, text_msg
		else:
			return None,None

# Fucntion to start a timer while waiting for a response
def receive_confirmation(timer):
	print("Starting timer for %s seconds" % timer)
	time = _time.perf_counter()
	while _time.perf_counter() < time + timer:
		clock = timer - (_time.perf_counter() - time)
		print("Countdown: %d"% clock)
		number, txt_msg = receive_txt()
		_time.sleep(0.2)
		if number == SE.NUM:
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

# Function to strobe the light
def strobe_light():
	# while not e.isSet():
    #     print(colour)
    #     time.sleep(0.5)
    #     event_is_set = e.wait(t)
    #     if event_is_set:
    #         print('stop led from flashing')
    #     else:
    #         print('leds off')
    #         time.sleep(0.5)

	# 	_time.sleep(1)
	# 	GPIO.output(22, GPIO.HIGH)
	# 	_time.sleep(1)
	# 	GPIO.output(22, GPIO.LOW)


# Function called when float switch detects water
# Alerts the user by SMS and waits for a response
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
			print("number %s NUM %s" % (number,SE.NUM))
			if number == SE.NUM:
				print("Received confirmation reply: %s" % txt_msg)
				if (txt_msg.find("yes") != -1) or (txt_msg.find("Yes") != -1):
					send_txt('Water Confirmed: float set to inactive, reset when ready')
					try:
						GPIO.remove_event_detect(17)
					except:
						pass
					check = False
					break
				elif (txt_msg.find("no") != -1) or (txt_msg.find("No") != -1):
					send_txt('Continuing detection')
					check = False
					break
				else:
					check = False
					print("error: confirmation not correctly spelt")
			_time.sleep(1.8)
		print("TIMER OUT")

# Fucntion called when button is pressed
# Used to reset the water sensor between bays
def button_pressed(channel):
	check = False
	check_time = _time.perf_counter()
	while GPIO.input(27) == 0:
		if _time.perf_counter() - check_time > 2:
			check = True
		
	if check == True:
		print("Button: Reseting on a new bay")
		send_txt('Button has been pressed. Do you wish to reset the Float switch? Reply yes/no within 2 minutes')
		
		confirmation = receive_confirmation(60)
		if confirmation == True:
			print("Resetting the float switch detection")
			try:
				GPIO.add_event_detect(17, GPIO.FALLING, callback=float_pressed, bouncetime=1500)  
			except:
				pass
		elif confirmation == False:
			send_txt('Reset Declined')
		elif confirmation == None:
			send_txt('Timer ran out')

# MAIN gets called on script startup
def main():
	print("Begining Startup")
	print("Curent Set Phone Number: %s" % SE.NUM)
	print("initialise")

	warmup()

	while True:
		print("try receive text")
		number, txt_msg = receive_txt()
		if txt_msg != None:
			print("text received")
			if txt_msg.find("change") != -1 or txt_msg.find("Change") != -1:
				print("Change number requested")
				new_num = txt_msg.split("#")
				new_num = new_num[len(new_num)-1]
				new_num = new_num[0:12]
				print("Number :%s." % new_num)
				print(len(new_num))
				print(len(SE.NUM))
				if len(new_num) == len(SE.NUM): 
					send_txt('Setting main number to %s\nconfirm yes/no within 1 minute' % new_num)
					confirmation = receive_confirmation(60)
					if confirmation == True:
						send_txt('Number Change Accepted, new number: %s' % new_num)
						print("New Number set to %s" % SE.NUM)
					elif confirmation == False:
						send_txt('Number Change Declined')
					elif confirmation == None:
						send_txt('Timer ran out')
		_time.sleep(2)

if __name__ == "__main__":
	try:
		main()
	except ValueError as e:
		print ("Error : {}".format(e))
