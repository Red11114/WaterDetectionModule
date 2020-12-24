#!/bin/bash
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                                AutoMinorLocator)
import pytz
print("importing complete")
fname='logs/21-12-2020_22-59-33.log'

data = {
    "time" : [],
    "voltage" : [],
    "current" : []
}
first = True
with open(fname, "r") as f:
    lines = f.readlines()

    for line in lines:
        if "DEBUG" in line:
            info = line.split("=")

            data["time"].append(info[0][:-11])
            data["voltage"].append(float(info[1][:-2]))
            data["current"].append(float(info[2][:-2]))
          
print("File complete")

timezone = pytz.timezone('Australia/Adelaide')

for i in range(len(data["time"])):
    data['time'][i]= datetime.datetime.strptime(data['time'][i][:-5],"%Y-%m-%d %H:%M:%S")
    data['time'][i] = timezone.localize(data['time'][i])

formatter = mdates.DateFormatter("%d %H:%M")
num = len(data["time"])/10

fig, ax = plt.subplots()
ax.plot(data["time"],data["current"])
# ax.plot(data["time"],data["current"], 'o', color='black')
ax.set_title("Curren vs Time")
ax.xaxis.set_major_formatter(formatter)
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)
# ax.xaxis.set_horizontalalignment('right')

print("Plot complete")
plt.savefig('Current_vs_Time.png')
print("first done")

fig2, ax2 = plt.subplots()
ax2.plot(data["time"],data["voltage"])
# ax2.plot(data["time"],data["voltage"], 'o', color='black')
ax2.set_title("Voltage vs Time")
# ax2.xaxis.set_major_locator(MultipleLocator(num))
ax2.xaxis.set_major_formatter(formatter)
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)

plt.savefig('Voltage_vs_Time.png')

plt.show()
