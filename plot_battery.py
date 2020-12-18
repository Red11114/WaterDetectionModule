#!/bin/bash
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                                AutoMinorLocator)
print("importing complete")
fname='logs/27-11-2020:13-30-34_log.txt'

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
            data["current"].append(float(info[2][:-1]))
            # print(line)
print("File complete")
# major_ticks = []
print(data)
# for i in data["time"]:
#     times = i.split(":")
#     print(times)
#     if int(times[1]) % 10 == 0:
#         major_ticks.append(int(times[1]))

fig, ax = plt.subplots()
ax.plot(data["time"],data["current"])
print(data["time"][1])
num = len(data["time"])/10
ax.xaxis.set_major_locator(MultipleLocator(num))
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)
# ax.xaxis.set_horizontalalignment('right')
print("Plot complete")

plt.show()
plt.savefig('Current_vs_Time.png')
print("first done")
fig2, ax2 = plt.subplots()
ax2.plot(data["time"],data["voltage"])

print(data["time"][1])
num = len(data["time"])/10
ax2.xaxis.set_major_locator(MultipleLocator(num))
# ax.xaxis.set_major_formatter(FormatStrFormatter('%s:%s:%s'))
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=0.2)
plt.savefig('Voltage_vs_Time.png')
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
