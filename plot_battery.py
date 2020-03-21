#!/bin/bash
import matplotlib.pyplot as plt

print("importing complete")
fname='21-3-2020:16-49-3_power.txt'

data = {
    "time" : [],
    "voltage" : [],
    "current" : []
}
first = True
with open('/home/pi/WaterDetectionModule/logs/%s'% fname, "r") as f:
    lines = f.readlines()

    for line in lines:
        if first == True:
            first = False
        else:
            info = line.split(",")
            data["time"].append(info[0])
            data["voltage"].append(float(info[1]))
            data["current"].append(float(info[2]))
            print(line)

plt.figure(0)

plt.plot(data["current"],data["voltage"])

plt.show()

print(data["time"])
print(data["voltage"])
