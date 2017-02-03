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

# This information should come from domoticz!!!
myLat = 52.095556
myLon = 4.316389

br = Buienradar()

#############################################################################
#                      Domoticz call back functions                         #
#############################################################################

def onStart():
    #Domoticz.Log("onStart called")
    createDevices()
    DumpConfigToDebug()
    #DumpConfigToLog()

    br.getBuienradarXML()
    br.getNearbyWeatherStation(myLat, myLon)
    br.getWeather()

def onConnect(Status, Description):
    Domoticz.Log("onConnect called")

def onMessage(Data, Status, Extra):
    Domoticz.Log("onMessage called")

def onCommand(Unit, Command, Level, Hue):
    Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

def onNotification(Data):
    Domoticz.Log("onNotification called: " + str(Data))

def onHeartbeat():
    #Domoticz.Log("onHeartBeat called")
    return

    # No nearby weather station detected, stop
    if bt.stationID == "":
        return

    nextUpdate = bt.lastUpdate + timedelta(minutes=15)
    if datetime.now() > nextUpdate:
        br.getBuienradarXML()
        br.getWeather()

def onDisconnect():
    Domoticz.Log("onHeartBeat called")

def onStop():
    Domoticz.Log("onStop called")

def sendMessage(data, method, url):
    Domoticz.Log("sendMessage called: " + str(data))

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

#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():

    if len(Devices) == 0:
        Domoticz.Device(Name="Temperature", Unit=1, TypeName="Temperature").Create()
        Domoticz.Log("Devices created.")
