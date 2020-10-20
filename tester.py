from EC25_Driver import smsModem

def main():
	print("start")
	modem = smsModem()
	modem.connect()
	modem.modeSelect("sms")
	modem.getAllSMS()
	modem.requestTime()
	modem.signalTest()
	modem.disconnect()
	print("end")

if __name__ == "__main__":
	main()