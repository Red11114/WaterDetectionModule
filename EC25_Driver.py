import serial
import time
import sys
from datetime import datetime

OPERATE_SMS_MODE = b'AT+CMGF=1\r'
RECEIVE_SMS = b'AT+CMGL="REC UNREAD"\r\n'
CLEAR_READ = b'AT+CMGD=1,1\r'
# ALLOW_AIRPLANE_MODE = b'AT+QCFG="airplanecontrol",1\r'
# MIN_FUNCTONALITY = b'AT+CFUN=0\r'
# NORMAL_FUNCTONALITY = b'AT+CFUN=1\r'
DISABLE_SLEEP = b'AT+QSCLK=0\r'
ENABLE_SLEEP = b'AT+QSCLK=1\r'
# ECHO_OFF = b'ATE0\r'
ENABLE_TIME_ZONE_UPDATE = b'AT+CTZU=1\r'
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
        
        i=0
        while i < 10:
            self.SendCommand(b'AT\r')
            time.sleep(1)
            data = self.ReadAll()
            if b'OK' in data:
                print("Serial comms active")
                return
            i=i+1
    
    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()
        
    def ReadLine(self):
        data = self.ser.readline()
        print(data)
        return data

    def ReadAll(self):
        data=self.ser.read(self.ser.in_waiting)
        print(data)
        return data

    def SendCommand(self,command, getline=True):
        self.ser.write(command)
        data = ''
        if getline:
            data=self.ReadLine()
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
        data = self.ReadAll()
        if b'+CMGL: ' in data:
            data = data.split(b'\n')
            texts = []
            for i in range(len(data)):
                if b'+CMGL: ' in data[i]:
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

    def refreshNetwork(self):
        self.SendCommand(DISCONNECT_NETWORK)
        time.sleep(1)
        self.SendCommand(ENABLE_TIME_ZONE_UPDATE)
        time.sleep(1)
        self.SendCommand(AUTO_NETWORK)
        time.sleep(1)
        self.SendCommand(NETWORK_REG)
        time.sleep(1)
        
    def requestTime(self):
        self.SendCommand(TIME_QUERY)
        time.sleep(1)
        data = self.ReadAll()
        if b'+CCLK: ' in data:
            data = data[:25]
            data = datetime.strptime(data.decode(), '+CCLK: "%y/%m/%d,%H:%M:%S')
            print(data)
        return data
    
    def signalTest(self):
        signal = b'99'
        i=0
        while signal == b'99' and i < 10:
                self.SendCommand(SIGNAL_CHECK)
                time.sleep(1)
                data = self.ReadAll()
                if b'OK' in data:
                    signal = data[6:8]
                    print(signal)
                i=i+1
                time.sleep(1)
        return signal