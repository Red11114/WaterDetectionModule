from INA260_MINIMAL import INA260
import time
import logging
from datetime import datetime

def main():
    ina260 = INA260(dev_address=0x40)
    ina260.reset_chip()

    time.sleep(1)
    datetime_object = datetime.now()
    print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second))
    try:
        logging.basicConfig(filename="logs/%s-%s-%s:%s-%s-%s_power.log" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second), filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    except:
        print("Log file could not be made")
        logging.error("Log file could not be made")

    print("Time,Bus Voltage (Volts),Charge Current (Amps)")
    logging.info("Time,Bus Voltage (Volts),Charge Current (Amps)")
    
    while True:
        bus_voltage = ina260.get_bus_voltage()
        charge_current = ina260.get_current()
        logging.info("%0.4f,%0.4f" % (bus_voltage,charge_current))
        print("%0.4f,%0.4f" % (bus_voltage,charge_current))
        time.sleep(0.1)
	
if __name__ == '__main__':  
    main()