from INA260_MINIMAL import INA260
import time
from datetime import datetime

def main():
    ina260 = INA260(dev_address=0x40)
    ina260.reset_chip()

    time.sleep(1)
    datetime_object = datetime.now()
    print("Current Date: %s-%s-%s, and Time: %s-%s-%s" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second))

    f = open("logs/%s-%s-%s:%s-%s-%s_power.txt" % (datetime_object.day,datetime_object.month,datetime_object.year,datetime_object.hour,datetime_object.minute,datetime_object.second),"a")
   
    print("Time,Bus Voltage (Volts),Charge Current (Amps)")
    f.write("Time,Bus Voltage (Volts),Charge Current (Amps)\n")
    # f.close()
    while True:
        datetime_object = datetime.now()
        bus_voltage = ina260.get_bus_voltage()
        charge_current = ina260.get_current()
        
        f.write("%s:%s:%s%s,%0.4f,%0.4f\n" % (datetime_object.hour,datetime_object.minute,datetime_object.second,str(datetime_object.microsecond),bus_voltage,charge_current))
        print("%s:%s:%s%s,%0.4f,%0.4f" % (datetime_object.hour,datetime_object.minute,datetime_object.second,str(datetime_object.microsecond),bus_voltage,charge_current))
        # f.write("%s:%s:%s%s\n" % (datetime_object.hour,datetime_object.minute,datetime_object.second,str(datetime_object.microsecond)[:]))
        # print("%s:%s:%s%s" % (datetime_object.hour,datetime_object.minute,datetime_object.second,str(datetime_object.microsecond)[:]))
        
        time.sleep(0.1)
    f.close()
if __name__ == '__main__':  
    main()