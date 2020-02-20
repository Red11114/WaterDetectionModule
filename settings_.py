# This is a file to hold all settings for the module

# Users master number
NUM = '+61448182742'

# Serial settings
SERIAL_PORT = '/dev/ttyUSB2'
SERIAL_RATE = 115200

# Define At command strings
OPERATE_SMS_MODE = 'AT+CMGF=1\r'
SEND_SMS = 'AT+CMGS="%s"\r'% NUM
RECEIVE_SMS = 'AT+CMGL="REC UNREAD"\r'
CLEAR_READ = 'AT+CMGD=1,1'

# Message to report after water detection
MSG = 'The float switch has been activated'