from EC25_Driver import smsModem
import time
import RPi.GPIO as GPIO

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

def main():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(FLOAT, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Float Switch pin
	GPIO.setup(DTR, GPIO.OUT, initial=GPIO.LOW) # DTR pin on 4g module
	GPIO.setup(W_DISABLE, GPIO.OUT, initial=GPIO.LOW) # W_DISABLE pin on 4g module
	GPIO.setup(RI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # RI pin on 4g module
	GPIO.setup(PERST, GPIO.OUT, initial=GPIO.LOW) # PERST pin on 4g module
	GPIO.setup(STROBE, GPIO.OUT, initial=GPIO.LOW) # Strobe pin
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin
	GPIO.output(DTR, GPIO.LOW)

	GPIO.output(DTR, GPIO.LOW)
	GPIO.output(W_DISABLE, GPIO.LOW)

	time.sleep(2)
	modem = smsModem()
	print("connect")
	modem.connect()
	print("config")
	modem.config()
	print("sig test")
	modem.signalTest()
	print("clear buffer")
	modem.ReadAll()

	
	print("waiting")
	time.sleep(2)
	# i = input("Enter text (or Enter to quit): ")
	# if not i:
	# 	print("excape")   # Enter key to quit
	# 	break
	
	# modem.refreshNetwork()
	# modem.modeSelect("sms")
	# modem.getSMS("READ")
	# modem.clearMessage(mode="read")
	# modem.getSMS("READ")
	# modem.requestTime()
	# modem.signalTest()
	# modem.sendMessage(message=b'holy moly i changed it')
	# print("entering Sleep")
	
	# GPIO.output(DTR, GPIO.HIGH)
	# GPIO.output(W_DISABLE, GPIO.HIGH)
	# GPIO.output(W_DISABLE, GPIO.LOW)
	GPIO.output(DTR, GPIO.LOW)
	time.sleep(0.5)
	modem.modeSelect("SLEEP")
	time.sleep(2)
	# GPIO.output(W_DISABLE, GPIO.HIGH)
	GPIO.output(DTR, GPIO.HIGH)
	
	
	while True:
		if b'DOWN' in modem.ReadAll():
			print("set GPIO")
			# GPIO.output(DTR, GPIO.HIGH)

		
		

	# #pull gpio pin high

	# # modem.connect()
	modem.disconnect()
	print("end")

if __name__ == "__main__":
	main()