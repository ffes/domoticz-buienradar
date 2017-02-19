#
#   Buienradar.nl Weather Lookup Plugin
#
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#   About the weather service:
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#
"""
<plugin key="Buienradar" name="Buienradar.nl (Weather lookup)" author="ffes" version="1.0" wikilink="" externallink="https://www.buienradar.nl/overbuienradar/gratis-weerdata">
    <params>
        <param field="Mode1" label="Latitude" width="200px" required="true" default=""/>
        <param field="Mode2" label="Longitude" width="200px" required="true" default=""/>
        <param field="Mode3" label="Update every x minutes" width="200px" required="true" default="15"/>
        <param field="Mode4" label="Temperature and humidity" width="200px" required="true">
            <options>
                <option label="Combined in one device" value="True" default="true" />
                <option label="Two separate devices" value="False" />
            </options>
        </param>
        <param field="Mode5" label="Include Wind chill in Wind device" width="200px" required="true">
            <options>
                <option label="Yes" value="True" default="true" />
                <option label="No" value="False"/>
            </options>
        </param>
    </params>
</plugin>
"""

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from buienradar import Buienradar

br = Buienradar()

#############################################################################
#                      Domoticz call back functions                         #
#############################################################################

def onStart():

    createDevices()
    #DumpConfigToDebug()
    #DumpConfigToLog()

    # This information should come from domoticz!!!
    myLat = br.parseFloatValue(Parameters["Mode1"])
    myLon = br.parseFloatValue(Parameters["Mode2"])

    if myLat == None or myLat == None:
        Domoticz.Log("Unable to parse coordinate")
        return False

    # Get the interval specified by the user
    interval = br.parseIntValue(Parameters["Mode3"])
    if interval == None:
        Domoticz.Log("Unable to parse interval")
        return False

    # Buienradar only updates the info every 10 minutes.
    # Allowing values below 10 minutes will not get you more info
    if interval < 10:
        Domoticz.Log("Interval too small")
        return False

    br.getBuienradarXML()
    br.getNearbyWeatherStation(myLat, myLon)

    fillDevices()

    Domoticz.Heartbeat(30)
    return True

def onHeartbeat():

    interval = br.parseFloatValue(Parameters["Mode3"])

    # Does the weather information needs to be updated?
    if br.needUpdate(interval):

        # Get new information and update the devices
        br.getBuienradarXML()
        fillDevices()

    return True

#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

def DumpConfigToDebug():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")

def UpdateDevice(Unit, nValue, sValue):

    # Make sure that the Domoticz device still exists before updating it.
    # It can be deleted or never created!
    if (Unit in Devices):

        Devices[Unit].Update(nValue, str(sValue))
        Domoticz.Debug("Update " + str(nValue) + ":'" + str(sValue) + "' (" + Devices[Unit].Name + ")")

#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():

    # Are there any devices?
    if len(Devices) != 0:
        # Could be the user deleted some devices, so do nothing
        return

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.

    # Add the temperature and humidity device(s)
    if Parameters["Mode4"] == "True":
        Domoticz.Device(Name="Temperature", Unit=3, TypeName="Temp+Hum").Create()
    else:
        Domoticz.Device(Name="Temperature", Unit=1, TypeName="Temperature").Create()
        Domoticz.Device(Name="Humidity", Unit=2, TypeName="Humidity").Create()

    # Add the barometer device
    Domoticz.Device(Name="Barometer", Unit=4, TypeName="Barometer").Create()

    # Add the wind (and wind chill?) device
    if Parameters["Mode5"] == "True":
        Domoticz.Device(Name="Wind", Unit=6, TypeName="Wind+Temp+Chill").Create()
    else:
        Domoticz.Device(Name="Wind", Unit=5, TypeName="Wind").Create()

    Domoticz.Log("Devices created.")

def fillDevices():

    # Did we get new weather info? Update all the possible devices
    if br.getWeather():

        # Temperature
        UpdateDevice(1, 0, str(round(br.temperature, 1)))

        # Humidity
        UpdateDevice(2, br.humidity, str(br.getHumidityStatus()))

        # Temperature and Humidity
        UpdateDevice(3, 0,
                    str(round(br.temperature, 1))
                    + ";" + str(br.humidity)
                    + ";" + str(br.getHumidityStatus()))

        # Barometer
        UpdateDevice(4, 0,
                    str(round(br.pressure, 1))
                    + ";" + str(br.getBarometerForecast()))

        # Wind
        UpdateDevice(5, 0, str(br.windBearing)
                    + ";" + br.getWindDirection()
                    + ";" + str(round(br.windSpeed * 10))
                    + ";" + str(round(br.windSpeedGusts * 10))
                    + ";0;0")

        # Wind and Wind Chill
        UpdateDevice(6, 0, str(br.windBearing)
                    + ";" + br.getWindDirection()
                    + ";" + str(round(br.windSpeed * 10))
                    + ";" + str(round(br.windSpeedGusts * 10))
                    + ";" + str(round(br.temperature, 1))
                    + ";" + str(br.getWindChill()))
