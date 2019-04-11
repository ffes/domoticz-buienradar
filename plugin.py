#
#   Buienradar.nl Weather Lookup Plugin
#
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#   About the weather service:
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#
#   Updates by G3rard, August 2017
#   Rain rate, Visibility, Solar Radiation, Rain forecast and Weather forecast added and some minor changes
#   Rain prediction from Rainfuture script by gerardvs - https://github.com/seventer/raintocome and Buienradar script from mjj4791 - https://github.com/mjj4791/python-buienradar
#
"""
<plugin key="Buienradar" name="Buienradar.nl (Weather lookup)" author="ffes" version="2.4.5" wikilink="https://github.com/ffes/domoticz-buienradar" externallink="https://www.buienradar.nl/overbuienradar/gratis-weerdata">
    <params>
        <param field="Mode2" label="Update every x minutes" width="200px" required="true" default="5"/>
        <param field="Mode3" label="Rain forecast timeframe in minutes" width="200px" required="true" default="30"/>
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
        <param field="Mode1" label="Rainrate options" width="200px" required="true">
            <options>
                <option label="Maximum rainrate" value=True default="true" />
                <option label="Average rainrate" value=False/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
                <option label="Logging" value="File"/>
            </options>
        </param>
    </params>
</plugin>
"""

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import requests
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from buienradar import Buienradar
from rainforecast import RainForecast

#############################################################################
#                      Domoticz call back functions                         #
#############################################################################
class BasePlugin:
    myLat       = myLon = 0
    br          = rf = None
    interval    = timeframe = None

    def onStart(self):
        #pylint: disable=undefined-variable
        global br, rf
        self.Error = False

        self.ShowMax = Parameters["Mode1"]
        if self.ShowMax == "" or self.ShowMax == "True":
            self.ShowMax = True

        if Parameters["Mode6"] != "Normal":
            Domoticz.Debugging(1)
            DumpConfigToLog()

        if CheckInternet() == False:
            self.Error = "You do not have a working internet connection."
            Domoticz.Error(self.Error)

        # Get the location from the Settings
        if not "Location" in Settings:
        	self.Error = "Location not set in Settings, please update your settings."
        	Domoticz.Error(self.Error)
        
        if self.Error == False:

	        # The location is stored in a string in the Settings
	        loc = Settings["Location"].split(";")
	        self.myLat = float(loc[0])
	        self.myLon = float(loc[1])
	        Domoticz.Debug("Coordinates from Domoticz: " + str(self.myLat) + ";" + str(self.myLon))

	        if self.myLat == None or self.myLon == None:
	            Domoticz.Log("Unable to parse coordinates")
	            return False

	        # Get the interval specified by the user
	        self.interval = int(Parameters["Mode2"])
	        if self.interval == None:
	            Domoticz.Log("Unable to parse interval, so set it to 10 minutes")
	            self.interval = 10

	        # Buienradar only updates the info every 10 minutes.
	        # Allowing values below 10 minutes will not get you more info
	        if self.interval < 5:
	            Domoticz.Log("Interval too small, changed to 5 minutes because Buienradar only updates the info every 5 minutes")
	            self.interval = 5

	        # Get the timeframe for the rain forecast
	        self.timeframe = int(Parameters["Mode3"])
	        if self.timeframe == None:
	            Domoticz.Log("Unable to parse timeframe, set to 30 minutes")
	            self.timeframe = 30
	        if self.timeframe < 5 or self.timeframe > 120:
	            Domoticz.Log("Timeframe must be >=5 and <=120. Now set to 30 minutes")
	            self.timeframe = 30

	        br = Buienradar(self.myLat, self.myLon, self.interval)
	        rf = RainForecast(self.myLat, self.myLon, self.timeframe, self.ShowMax)

	        # Check if devices need to be created
	        createDevices()

	        # Check if images are in database
	        if 'BuienradarRainLogo' not in Images: Domoticz.Image('buienradar.zip').Create()
	        if 'BuienradarLogo' not in Images: Domoticz.Image('buienradar-logo.zip').Create()

	        # Get data from Buienradar
	        br.getBuienradarXML()
	        br.getNearbyWeatherStation()

	        # Fill the devices with the Buienradar values
	        fillDevices()

	        Domoticz.Heartbeat(30)

    def onHeartbeat(self):
        if CheckInternet() == False:
            self.Error = "You do not have a working internet connection."
            Domoticz.Error(self.Error)
        elif CheckInternet() == True and self.Error == "You do not have a working internet connection.":
            self.Error = False

        if self.Error == False:
            # Does the weather information needs to be updated?
            global br
            if br.needUpdate():
                # Get new information and update the devices
                br.getBuienradarXML()
                fillDevices()
        else:
            Domoticz.Error(self.Error)

_plugin = BasePlugin()

def onStart():
    _plugin.onStart()

def onHeartbeat():
    _plugin.onHeartbeat()

#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

def CheckInternet():
    try:
        requests.get(url='http://www.google.com/', timeout=5)
        return True
    except requests.ConnectionError:
        return False

def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"] + "plugin.log", "a")
        f.write(Message + "\r\n")
        f.close()
    Domoticz.Debug(Message)

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            LogMessage( "'" + x + "':'" + str(Parameters[x]) + "'")
    LogMessage("Device count: " + str(len(Devices)))
    for x in Devices:
        LogMessage("Device:           " + str(x) + " - " + str(Devices[x]))
        LogMessage("Internal ID:     '" + str(Devices[x].ID) + "'")
        LogMessage("External ID:     '" + str(Devices[x].DeviceID) + "'")
        LogMessage("Device Name:     '" + Devices[x].Name + "'")
        LogMessage("Device nValue:    " + str(Devices[x].nValue))
        LogMessage("Device sValue:   '" + Devices[x].sValue + "'")
        LogMessage("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or AlwaysUpdate == True:
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return

#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():

    # Are there any devices?
    ###if len(Devices) != 0:
        # Could be the user deleted some devices, so do nothing
        ###return

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.

    # Add the temperature and humidity device(s)
    if Parameters["Mode4"] == "True":
        if 3 not in Devices:
            Domoticz.Device(Name="Temperature", Unit=3, TypeName="Temp+Hum", Used=1).Create()
    else:
        if 1 and 2 not in Devices:
            Domoticz.Device(Name="Temperature", Unit=1, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name="Humidity", Unit=2, TypeName="Humidity", Used=1).Create()

    # Add the barometer device
    if 4 not in Devices:
        Domoticz.Device(Name="Barometer", Unit=4, TypeName="Barometer", Used=1).Create()

    # Add the wind (and wind chill?) device
    if Parameters["Mode5"] == "True":
        if 6 not in Devices:
            Domoticz.Device(Name="Wind", Unit=6, TypeName="Wind+Temp+Chill", Used=1).Create()
    else:
        if 5 not in Devices:
            Domoticz.Device(Name="Wind", Unit=5, TypeName="Wind", Used=1).Create()

    if 7 not in Devices:
        Domoticz.Device(Name="Visibility", Unit=7, TypeName="Visibility", Used=1).Create()
    if 8 not in Devices:
        Domoticz.Device(Name="Solar Radiation", Unit=8, TypeName="Solar Radiation", Used=1).Create()
    if 9 not in Devices:
        Domoticz.Device(Name="Current Rain rate", Unit=9, TypeName="Rain", Used=1).Create()
    if 10 not in Devices:
        Domoticz.Device(Name="Rain forecast", Unit=10, TypeName="Rain", Used=1).Create()
    if 11 not in Devices:
        Domoticz.Device(Name="Weather forecast", Unit=11, TypeName="Text", Used=1).Create()

    Domoticz.Log("Devices checked and created/updated if necessary")

def fillDevices():

    # Did we get new weather info? Update all the possible devices
    if br.getWeather():

        # Temperature
        if br.temperature != None:
            UpdateDevice(1, 0, str(round(br.temperature, 1)))

        # Humidity
        if br.humidity != None:
            UpdateDevice(2, br.humidity, str(br.getHumidityStatus()))

        # Temperature and Humidity
        if br.temperature != None and br.humidity != None:
            UpdateDevice(3, 0,
                    str(round(br.temperature, 1))
                    + ";" + str(br.humidity)
                    + ";" + str(br.getHumidityStatus()))

        # Barometer
        if br.pressure != None:
            UpdateDevice(4, 0,
                    str(round(br.pressure, 1))
                    + ";" + str(br.getBarometerForecast()))

        # Wind
        if br.windBearing != None and br.windSpeed != None and br.windSpeedGusts != None:
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

        # Visibility
        if br.visibility != None:
            UpdateDevice(7, 0, str(round((br.visibility/1000), 1))) # Visibility is m in Buienradar and km in Domoticz

        # Solar Radiation
        if br.solarIrradiance != None:
            UpdateDevice(8, 0, str(br.solarIrradiance))

        # Rain rate
        if br.rainRate == None: br.rainRate = 0
        UpdateDevice(9, 0, str(br.rainRate*100)+";"+str(br.rainToday))

        # Rain forecast
        result = rf.get_precipfc_data() ###30 nog nakijken
        UpdateDevice(10, 0, str(result['averagemm']*100)+";"+str(result['average']))

        if br.weatherForecast != None:
            UpdateDevice(11, 0, str(br.weatherForecast))

# Synchronise images to match parameter in hardware page
def UpdateImage(Unit, Logo):
    if Unit in Devices and Logo in Images:
        if Devices[Unit].Image != Images[Logo].ID:
            #Domoticz.Log("Device Image update: 'Buienradar', Currently " + str(Devices[Unit].Image) + ", should be " + str(Images[Logo].ID))
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=str(Devices[Unit].sValue), Image=Images[Logo].ID)
    return
