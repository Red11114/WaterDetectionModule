from EC25_Driver import smsModem
import time

def main():
	print("start")
	modem = smsModem()
	# modem.saveConfig()
	# modem.reset()
	modem.connect()
	while True:
		print("waiting")
		time.sleep(1)
		# i = input("Enter text (or Enter to quit): ")
		# if not i:
		# 	print("excape")   # Enter key to quit
		# 	break
	print("Your input:", i)
	# modem.refreshNetwork()
	# modem.modeSelect("sms")
	# modem.getSMS("READ")
	# modem.clearMessage(mode="read")
	# modem.getSMS("READ")
	# modem.requestTime()
	# modem.signalTest()
	# # modem.sendMessage(message=b'holy moly i changed it')
	# modem.modeSelect("sleep")
	
	# #pull gpio pin high

	# # modem.connect()
	modem.disconnect()
	print("end")

if __name__ == "__main__":
	main()