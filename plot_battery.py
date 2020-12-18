#!/bin/bash
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                                AutoMinorLocator)
print("importing complete")
fname='logs/14-12-2020_8-32-58.log'

data = {
    "time" : [],
    "voltage" : [],
    "current" : []
}
first = True
with open(fname, "r") as f:
    lines = f.readlines()

    for line in lines:
        # if first == True:
        #     first = False
        # else:
        if "DEBUG" in line:
            info = line.split("=")

            data["time"].append(info[0][:-11])
            data["voltage"].append(float(info[1][:-2]))
            data["current"].append(float(info[2][:-2]))
            # print(line)
print("File complete")
# major_ticks = []

for i in range(len(data["time"])):
    data['time'][i]= [datetime.datetime.strptime(data['time'][i][:-4],"%Y-%m-%d %H:%M:%S,")]

# for i in data["time"]:
#     times = i.split(":")
#     print(times)
#     if int(times[1]) % 10 == 0:
#         major_ticks.append(int(times[1]))
formatter = mdates.DateFormatter("%d %H:%M")

fig, ax = plt.subplots()
ax.plot(data["time"],data["current"])
print(data["time"][1])
num = len(data["time"])/10
ax.xaxis.set_major_formatter(formatter)
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)
# ax.xaxis.set_horizontalalignment('right')
print("Plot complete")

# plt.show()
plt.savefig('Current_vs_Time.png')
print("first done")
fig2, ax2 = plt.subplots()
ax2.plot(data["time"],data["voltage"])

print(data["time"][1])
num = len(data["time"])/10
# ax2.xaxis.set_major_locator(MultipleLocator(num))
ax2.xaxis.set_major_formatter(formatter)
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)
plt.savefig('Voltage_vs_Time.png')
plt.show()
print("SAVED")
# fig2, ax2 = plt.subplots()
# ax2.plot(data["time"],data["voltage"])
# # ax2.xaxis.set_major_locator(MultipleLocator(50))
# # ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
# plt.xticks(rotation='vertical')
# plt.subplots_adjust(bottom=0.3)
# ax.xaxis.set_horizontalalignment('right')
# print(data["time"])
# print(data["voltage"])
# plt.show()
