#set wifi on and off
import os

def main():
    status = check_wifi_status()
                 
    if status == "UP":
        turn_wifi_off()
    elif status == "DOWN":
        turn_wifi_on()
    else:
        print("error received from wifi interface")
    
def check_wifi_status():
    cmd = 'cat /sys/class/net/wlan0/operstate'
	response = os.system(cmd)
    return response

def turn_wifi_on():
    cmd = 'ifconfig wlan0 up'
	response = os.system(cmd)
    return response

def turn_wifi_off():
    cmd = 'ifconfig wlan0 down'
	response = os.system(cmd)
    return response
