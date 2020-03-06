# Water Detection Module

This device is designed to alert the user to the presence of water at the end of an irrigation bay.
It does this by polling a float switch for activity and will alert the user by text if water has arrived.
The system is comprised of a Raspberry Pi running Raspbian Buster Lite and a SixFab v2 LTE shield with a Quectel EC25-AUT module.
The float switch used can be any normally open float switch, as long as it is connected to GPIO 17.
A normally open push button is connected to GPIO 27 and is used for reseting the device when moving it to another bay.
There is a 5v relay connected to GPIO 22 which activates a strobe light.

## Setting up a new Raspbian Lite SD card

Download the Raspberry Pi Imaging tool from the following link
```
https://www.raspberrypi.org/downloads/
```
Install the program and insert a fromatted SD card into the computer
Run Raspberry Pi imager and select; Choose OS > Raspbian (other) > Raspbian Lite
Select the SD Card to image and click Write

Once writen the SD card will only be readable on a Linux machine, so ensure it is pluged into a Linux commputer for the next steps

### Enable SSH

Open a terminal and navigate to the boot directory of the SD card
To enable SSH create a blank file called ssh
```
touch ssh
```

### Add network info

Open a terminal and navigate to the boot directory of the SD card
Create a file called wpa_supplicant.conf
```
touch wpa_supplicant.conf
```
Edit the file
```
gedit wpa_supplicant.conf
```
Add the following with your network information
```
country=AU
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="NETWORK-NAME"
    psk="NETWORK-PASSWORD"
}
```

Eject the SD card from your computer, then pull it out and plug it into the Raspberry Pi

### Login over WiFi

The default user will be "pi" with the password "raspberry"
NOTE: Your computer must be on the same WiFi as the Raspberry Pi

#### Linux:
Open a terminal
```
ssh pi@raspberrypi.local
```
If prompted to continue connecting respond "yes"

#### Windows:
Install Putty

If you already have Putty installed, skip to the next section.

Browse to: https://www.putty.org
Download the 64-bit MSI (Windows Installer)
Open it to run the installer (if asked for permission, click Yes)

Launch Putty
Set the Host Name (or IP address) field to raspberrypi.local
By default the Port should be set to 22 and Connection type should be set to SSH
Click Open
If you see a Security Alert select Yes
A new terminal window should appear prompting you for a user name
The default user name is: pi
The default password is: raspberry

### Change Hostname and Password

After SSHing into the Pi for the first time, the hostname and password should be changed immediately by typing
```
sudo raspi-config
```
Select the Change User Password option and when prompted enter the new password twice

Select Network Options followed by Hostname
Enter the new hostname of the Pi making sure to take not of what it has been changed to

While in the raspi-config its also a good idea for new installs to expand the filesystem so the Pi has access to the entire SD card
Do this by selecting the Advanced Option and Expand Filesystem

Save the changes and the device will reboot
NOTE: After changing the hostname the ssh command must include the new hostname
Example:
```
ssh pi@testpi2.local
```

### Get Updates

Once connected over WiFi the Pi should be updated by entering the following commands
```
sudo apt-get update -y
sudo apt-get upgrade -y
```

## Aquiring and configuring git repository

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Andrew Vermeeren** - *Initial work* - [Red11114](https://github.com/Red11114)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
