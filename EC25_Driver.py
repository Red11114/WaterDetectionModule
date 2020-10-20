import serial
import time
import sys

OPERATE_SMS_MODE = b'AT+CMGF=1\r'
RECEIVE_SMS = b'AT+CMGL="REC UNREAD"\r\n'
CLEAR_READ = b'AT+CMGD=1,1\r'
# ALLOW_AIRPLANE_MODE = b'AT+QCFG="airplanecontrol",1\r'
# MIN_FUNCTONALITY = b'AT+CFUN=0\r'
# NORMAL_FUNCTONALITY = b'AT+CFUN=1\r'
DISABLE_SLEEP = b'AT+QSCLK=0\r'
ENABLE_SLEEP = b'AT+QSCLK=1\r'
# ECHO_OFF = b'ATE0\r'
ENABLE_TIME_ZONE_UPDATE = b'AT+CTZU=3\r'
TIME_QUERY = b'AT+CCLK?\r'
SIGNAL_CHECK = b'AT+CSQ\r'
NETWORK_REG = b'AT+CREG=1\r'
AUTO_NETWORK = b'AT+COPS=0\r'
DISCONNECT_NETWORK = b'AT+COPS=2\r'

class smsModem(object):
    def __init__(self):
        self.ser = serial.Serial(port='/dev/ttyAMA0', baudrate=115200, timeout=2, write_timeout=2)
        #... xonxoff = False, rtscts = False, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE)
        time.sleep(1)
  
    def connect(self):
        if not self.ser.is_open:
            self.ser.open()
    
    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()

    def SendCommand(self,command, getline=True):
        self.ser.write(command)
        data = ''
        if getline:
            data=self.ReadLine()
        return data 

    def ReadLine(self):
        data = self.ser.readline()
        print(data)
        return data

    def modeSelect(self,mode):
        if mode == "sms":
            self.SendCommand(OPERATE_SMS_MODE)
        elif mode == "sleep":
            self.SendCommand(ENABLE_SLEEP)

    def getAllSMS(self):
        self.ser.flushInput()
        self.ser.flushOutput()

        self.SendCommand(RECEIVE_SMS)
        data = self.ser.readall()
        print(data)
        if data.find(b'+CMGL: ') != -1:
            data = data.split(b'\n')
            texts = []
            for i in range(len(data)):
                if data[i].find(b'+CMGL: ') != -1:
                    temp = data[i].split(b',')
                    text = dict(number=temp[2][1:-1].decode(),date=temp[4][1:].decode(),
                    time=temp[5][:-2].decode(),message=data[i+1][:-1].decode())
                    texts.append(text)
            print(texts)
            return texts
        else:
            return data

    def sendMessage(self, recipient="+61448182742", message="TextMessage.content not set."):
        self.SendCommand(OPERATE_SMS_MODE)
        time.sleep(1)
        self.SendCommand('''AT+CMGS="''' + recipient + '''"\r''')
        time.sleep(1)
        self.SendCommand(message + "\r")
        time.sleep(1)
        self.SendCommand(chr(26))
        time.sleep(1)

    





    
# sms.connectPhone()
# sms.sendMessage()
# sms.disconnectPhone()
# print "message sent successfully"

# h = HuaweiModem()
# h.GetAllSMS()