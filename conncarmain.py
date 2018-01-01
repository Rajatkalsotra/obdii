"""
#
# Author:       L. Saetta
# created:      27 december 2017
# last update:  29/12/2017
#
# published under MIT license (see LICENSE file)
"""

# pylint: disable=invalid-name

import json
import time
import datetime
import sys
import configparser
import os
from Device import Device
from OBDII import OBDII
from OBDIISimulator import OBDIISimulator

# Configuration
#  to format datetime
STFORMAT1 = "%d-%m-%Y %H:%M:%S"
STFORMAT2 = "%d-%m-%Y"

# send a msg every 5 sec.
sleepTime = 5
#the name of MQTT topic where msgs are sent
TOPIC_NAME = 'cardata'


# read configuration from gateway.ini file
# read OBD2_HOME env variable
OBD2HOME = os.getenv('OBD2_HOME')

config = configparser.ConfigParser()
config.read(OBD2HOME + '/gateway.ini')
msgLogging = config['DEFAULT']['msgLogging']
carID = config['DEFAULT']['carID']

# file name for local logging
FNAME = OBD2HOME + "/msgs" + datetime.datetime.now().strftime(STFORMAT2) + ".log"

#
# createJSONMsg()
# create the msg in JSON format starting from OBDII readings
#
def createJSONMsg():
    msg = {}
    
    if runMode == "SIMUL":
       # using the simulator
       msg = obdii.getMessage()
       msg['CARID'] = carID 
    else:
       # read data from OBDII
       msg = obdii.getMessage()
       msg['CARID'] = carID
    
    # format in JSON
    msgJson = json.dumps(msg)
    
    return msgJson


#
# **** Main **** 
#

#
# Test if simulation mode (no acquiring data from OBDII)
#
# runMode = SIMUL|ACQUIRE|NULL (null means ACQUIRE)
parLenght = len(sys.argv)

if parLenght >= 2:
    runMode = sys.argv[1]
else:
    runMode = "ACQUIRE"

print("\n")
print("Program started...")
print("RUN MODE: ", runMode)

# MQTT connectivity is encapsulated in the Device class
# see Device.py
gateway = Device()


# try connecting in loop
# to handle case in which initially no network connection
while gateway.isConnected() != True:
    try:
        gateway.connect()
    except:
        print('Error in MQTT connection !')

    time.sleep(sleepTime)


#
# connectivity to OBDII interface
#
if runMode == "ACQUIRE":
    obdii = OBDII()
else:
    obdii = OBDIISimulator()

#
# main loop
#

if msgLogging == "YES":
    pFile = open(FNAME, "w")

# wait for MQTT connection OK
# (at this point should be connected)
gateway.wait_for_conn_ok()

print('Mqtt connection OK !\n')

nMsgs = 0

while True:
    nMsgs = nMsgs + 1
    print('Sending msg number: ', nMsgs)

    # create the msg to send from data
    msgJson = createJSONMsg()

    try:
        gateway.publish(TOPIC_NAME, msgJson)
    except:
        print('Error in sending...')

    if msgLogging == "YES":
        # log msg on file...
        pFile.write(msgJson)
        pFile.write('\n')

    time.sleep(sleepTime)


if msgLogging == "YES":
    pFile.close()
