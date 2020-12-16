# Water Detection Module

This device is designed to alert the user to the presence of water at the end of an irrigation bay. It does this by polling a float switch for activity and will alert the user by text if water has arrived. The system is comprised of a Raspberry Pi running Raspbian Buster Lite and a SixFab v2 LTE shield with a Quectel EC25-AUT module. The float switch used can be any normally open float switch, as long as it is connected to GPIO 17. A normally open push button is connected to GPIO 27 and is used for reseting the device when moving it to another bay. There is a 5v relay connected to GPIO 22 which activates a strobe light.

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

In VSCode with rmate installed
```
ssh -R 52698:127.0.0.1:52698 pi@hostname
```

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
### Enable SPI and I2C

```
sudo raspi-config
```

Select Interface Options > I2C/SPI

Save the changes and reboot

```
sudo reboot
```

### Check I2C and SPI connection

For 12C run the following command and compare with result
```
sudo i2cdetect -y 1
```
Result:
```

```
For SPI run the following command and compare with result
```
ls -l /dev/spidev*
```
Result:
```

```

### Get Updates

Once connected over WiFi the Pi should be updated by entering the following commands
```
sudo apt-get update -y
sudo apt-get upgrade -y
```

## Aquiring and configuring git repository

First install git 
```
sudo apt-get install git
```
Then type "y" when prompted to install

To clone the Git repository for the standalone Water Detection Module type
```
git clone https://github.com/Red11114/WaterDetectionModule.git
```
### Creating a Virtual Environment

Install **pip** first
```
sudo apt-get install python3-pip
```
Then install **venv**
```
sudo apt install python3-venv
```
**The following steps can be skipped by typing**
```
source setup-venv.sh
```
**It will create the venv and install all packages**

Now create a virtual environment 
```
python3 -m venv env
```

### Activate your virtual environment:

When developing, the code must be run using the virtual environment

To activate the virtual environment type
```
source env/bin/activate
```
To deactivate type
```
deactivate
```

### Installing required packages

First activate the virtual environment
```
pip install -r requirements.txt
```
To check currently installed packages type
```
pip freeze
```
To save currently installed packages to a new file type
```
pip freeze > requirements.txt
```
## Boot settings

To add and enable services on boot use systemd

```
sudo cp services/detection.service /etc/systemd/system
```

Then enable them to start on boot

Or quick start them only on this cycle

```
sudo systemctl enable detection.service
sudo systemctl start detection.service
```

## Edit of privliges file
```
sudo visudo
```
under the line (25),

%sudo   ALL=(ALL:ALL) ALL

add the following
```
hostname ALL=(ALL) NOPASSWORD: /home/hostname/waterdetectionmodule/wifi.sh
```
change permissions of file:
```
sudo chmod root:toot /home/username/waterdetectionmodule/wifi.sh
sudo chmod 700 /home/username/waterdetectionmodule/wifi.sh
```

## Check Clock update sync
```
timedatectl status
```
Response:
```
Local time: Mon 2020-11-30 14:26:11 ACDT
           Universal time: Mon 2020-11-30 03:56:11 UTC
                 RTC time: n/a
                Time zone: Australia/Adelaide (ACDT, +1030)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```
Set NTP:
```
sudo timedatectl set-ntp true
```
or,
```
sudo systemctl start systemd-timesyncd.service 
```
Set RTC:
```
timedatectl set-local-rtc 0
```

## Running the test script

This script should test importing of all required dependencies.

It should also probe the LTE module for connection and issue general health check AT commands and show the result to the user.

It should also wait for the user to press the button and float switch to make sure they are connected correctly, then flash the strobe a few times.

Explain how to run the test script and the expected outcomes.

Give explanation for the soloutions to errors.

## Updates Deployment

How to set a module to connect to a WiFi modem (pull sd card and update Wpa_configuration.conf)

SSH into the pi and pull updates from github

run test script

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Andrew Vermeeren** - *Initial work* - [Red11114](https://github.com/Red11114)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Mark Jessop for helping with some general issues and suggesting good ideas to implement