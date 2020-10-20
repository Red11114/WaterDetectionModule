from EC25_Driver import smsModem

def main():
	print("start")
	modem = smsModem()
	modem.connect()
	modem.modeSelect("sms")
	modem.getAllSMS()
	print("end")

if __name__ == "__main__":
	main()