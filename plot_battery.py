#!/bin/bash
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
print("importing complete")
fname='/home/andrew/Documents/WaterDetectionModule/21-3-2020:23-53-35_power.txt'

data = {
    "time" : [],
    "voltage" : [],
    "current" : []
}
first = True
with open(fname, "r") as f:
    lines = f.readlines()

    for line in lines:
        if first == True:
            first = False
        else:
            info = line.split(",")
            data["time"].append(info[0])
            data["voltage"].append(float(info[1]))
            data["current"].append(float(info[2]))
            # print(line)

# major_ticks = []
# for i in data["time"]:
#     times = i.split(":")
#     print(times)
#     if int(times[1]) % 10 == 0:
#         major_ticks.append(int(times[1]))

fig, ax = plt.subplots()
ax.plot(data["time"],data["current"])
# ax.xaxis.set_major_locator(MultipleLocator(50))
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.3)
# ax.xaxis.set_horizontalalignment('right')

# plt.savefig('Current vs Time.png')

fig2, ax2 = plt.subplots()
ax2.plot(data["time"],data["voltage"])
# ax2.xaxis.set_major_locator(MultipleLocator(50))
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.3)
# ax.xaxis.set_horizontalalignment('right')
# print(data["time"])
# print(data["voltage"])
plt.show()