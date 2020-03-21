#!/bin/bash
import matplotlib.pyplot as plt

print("importing complete")
fname='/home/andrew/Documents/WaterDetectionModule/21-3-2020:17-57-40_power.txt'

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

plt.figure(0)
plt.plot(data["time"],data["current"])
plt.show()
plt.savefig('Current vs Time.png')

# print(data["time"])
# print(data["voltage"])
