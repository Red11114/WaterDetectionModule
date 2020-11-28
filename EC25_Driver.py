import serial
import time
import sys
from datetime import datetime
import pytz

# Define At command strings
SAVE_PARAMETERS = b'AT&W'
LOAD_PARAMETERS = b'ATZ'
OPERATE_SMS_MODE = b'AT+CMGF=1\r'
RECEIVE_UNREAD = b'AT+CMGL="REC UNREAD"\r\n'
RECEIVE_READ = b'AT+CMGL="REC READ"\r\n'
RECEIVE_ALL = b'AT+CMGL="ALL"\r\n'
CLEAR_READ = b'AT+CMGD=1,1\r'
CLEAR_ALL = b'AT+CMGD=1,4\r'
MIN_FUNCTONALITY = b'AT+CFUN=0\r'
NORMAL_FUNCTONALITY = b'AT+CFUN=1\r'
DISABLE_SLEEP = b'AT+QSCLK=0\r'
ENABLE_SLEEP = b'AT+QSCLK=1\r'
ENABLE_TIME_ZONE_UPDATE = b'AT+CTZU=1\r'
TIME_QUERY = b'AT+CCLK?\r'
SIGNAL_CHECK = b'AT+CSQ\r'
NETWORK_REG = b'AT+CREG=1\r'
AUTO_NETWORK = b'AT+COPS=0\r'
DISCONNECT_NETWORK = b'AT+COPS=2\r'
RI_MODE_PHYSICAL = b'AT+QCFG="risignaltype","physical"\r'
RI_SMS_CONFIG = b'AT+QCFG="urc/ri/smsincoming","pulse",120,1\r'
TURN_OFF = b'AT+QPOWD=1\r'

class smsModem(object):
    def __init__(self):
        self.ser = serial.Serial(port='/dev/ttyAMA0', baudrate=115200, write_timeout=2)
    
    def config(self):
        self.SendCommand(RI_MODE_PHYSICAL)
        self.ReadLine()
        self.SendCommand(RI_SMS_CONFIG)
        self.ReadLine()
        self.SendCommand(NORMAL_FUNCTONALITY)
        self.ReadLine()
        self.SendCommand(NETWORK_REG)
        self.ReadLine()
        self.SendCommand(OPERATE_SMS_MODE)
        self.ReadLine()
        self.SendCommand(ENABLE_SLEEP)
        self.ReadLine()

    def connect(self, timeout=10):
        if not self.ser.is_open:
            self.ser.open()

        self.ser.flushInput()
        self.ser.flushOutput()

        temp_time = time.perf_counter()
        while (time.perf_counter() - temp_time < timeout):
            self.SendCommand(b'AT\r')
            time.sleep(1)
            data = self.ReadAll()
            if b'OK' in data:
                print("Serial comms active")
                return
        print("Serial comms is inactive")
    
    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()
        
    def reset(self):
        self.SendCommand(LOAD_PARAMETERS)

    def saveConfig(self):
        self.SendCommand(SAVE_PARAMETERS)

    def ReadLine(self):
        data = self.ser.readline()
        time.sleep(0.2)
        print(data)
        return data

    def ReadAll(self):
        data=self.ser.read(self.ser.in_waiting)
        time.sleep(0.2)
        print(data)
        return data

    def SendCommand(self,command, getline=True):
        self.ser.write(command)
        time.sleep(0.5)
        
        data = ''
        if getline:
            data=self.ReadLine()
            time.sleep(0.2)
        return data 

    def modeSelect(self,mode):
        if mode == "NORM":
            self.SendCommand(NORMAL_FUNCTONALITY)
            self.ReadLine()
        elif mode == "MIN":
            self.SendCommand(MIN_FUNCTONALITY)
            self.ReadLine()
        elif mode == "OFF":
            self.SendCommand(TURN_OFF)
            self.ReadLine()

    def getSMS(self,mode="UNREAD"):
        self.ser.flushInput()
        self.ser.flushOutput()

        if mode == "UNREAD":
            self.SendCommand(RECEIVE_UNREAD)
        elif mode == "READ":
            self.SendCommand(RECEIVE_READ)
        elif mode == "ALL":
            self.SendCommand(RECEIVE_ALL)

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
            return None
    
    def clearMessage(self,mode="ALL"):
        if mode == "READ":
            self.SendCommand(CLEAR_READ)
        elif mode == "ALL":
            self.SendCommand(CLEAR_ALL)
        time.sleep(4)
        print(self.ReadAll())

    def sendMessage(self, recipient=b'+61448182742', message=b'TextMessage.content not set.'):
        self.SendCommand(b'AT+CMGS="%s"\r'% recipient)
        self.SendCommand(b'%b\r' % message)
        self.SendCommand(b'\x1a')
        self.ReadLine()
        self.ReadAll()

    def refreshNetwork(self):
        self.SendCommand(DISCONNECT_NETWORK)
        self.ReadLine()
        self.SendCommand(ENABLE_TIME_ZONE_UPDATE)
        self.ReadLine()
        self.SendCommand(AUTO_NETWORK)
        self.ReadLine()
        self.SendCommand(NETWORK_REG)
        self.ReadLine()
        
    def requestTime(self):
        self.SendCommand(TIME_QUERY)
        time.sleep(1)
        data = self.ReadAll()
        if b'+CCLK: ' in data:
            data = data[:25]
            result = datetime.strptime(data.decode(), '+CCLK: "%y/%m/%d,%H:%M:%S')
            timezone = pytz.timezone('Australia/Adelaide')
            result = timezone.localize(result)
        return result.now()
    
    def signalTest(self, timeout=10):
        signal = b'99'
        temp_time = time.perf_counter()
        while signal == b'99' and (time.perf_counter() - temp_time < timeout):
                self.SendCommand(SIGNAL_CHECK)
                time.sleep(1)
                data = self.ReadAll()
                if b'OK' in data:
                    signal = data[6:8]
                    print(signal)
                time.sleep(1)
        return signal
