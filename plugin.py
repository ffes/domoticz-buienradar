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

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
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

    Domoticz.Device(Name="Temperature", Unit=1, TypeName="Temperature").Create()
    Domoticz.Device(Name="Wind", Unit=2, TypeName="Wind+Temp+Chill").Create()
    Domoticz.Log("Devices created.")

def fillDevices():

    if br.getWeather():

        UpdateDevice(1, 0, str(br.temperature))
        UpdateDevice(2, 0, str(br.windBearing)
                    + ";" + br.getWindDirection()
                    + ";" + str(round(br.windSpeed * 10))
                    + ";" + str(round(br.windSpeedGusts * 10))
                    + ";" + str(round(br.temperature, 1))
                    + ";" + str(br.getWindChill()))
