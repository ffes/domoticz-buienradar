#
#   Buienradar.nl Weather Lookup Plugin
#
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#   About the weather service:
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta

class Buienradar:

    def __init__(self):
        self.lastUpdate = datetime.now()
        self.stationID = ""
        self.tree = None
        resetWeatherValues(self)


    def resetWeatherValues(self):

        self.observationDate = datetime.now()
        self.temperature = None             # degrees Celsius
        self.windSpeed = None               # m/s
        self.windDirection = None           # degrees
        self.windSpeedGusts = None          # m/s

    #
    # Calculate the great circle distance between two points
    # on the earth (specified in decimal degrees)
    #

    def haversine(self, lat1, lon1, lat2, lon2):

        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [ lat1, lon1, lat2, lon2 ])

        # Haversine formula
        dlat = abs(lat2 - lat1)
        dlon = abs(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = c * 6367
        return km

    #
    # Get the weather information from http://xml.buienradar.nl
    #

    def getBuienradarXML(self, file = ''):

        self.tree = None

        if file != '':
            self.tree = ET.ElementTree(file=file)
            return

        url = 'http://xml.buienradar.nl/'
        try:
            Domoticz.Log('Retrieve weather data from ' + url)
            xml = urllib.request.urlopen(url, data=None)
        except urllib.error.HTTPError as e:
            Domoticz.Log("HTTP error: " + str(e) + " URL: " + url)
            return

        self.tree = ET.parse(xml)
        self.lastUpdate = datetime.now()

    #
    # Find the weather station nearby
    #

    def getNearbyWeatherStation(self, myLat, myLon):

        # Is the tree set?
        if self.tree == None:
            return

        # Start distance far away
        distance = 10000.0

        # Go through all the weather stations
        for stations in self.tree.iterfind('weergegevens/actueel_weer/weerstations'):

            for station in stations.findall('weerstation'):

                # What is the temperature at this station?
                temp = self.parseFloatValue(station.find('temperatuurGC').text)

                # If no is temperature set, skip this entry
                # Many weather stations only measure wind speed
                # They are not useful for weather information in domoticz
                if temp == None:
                    continue

                # Where is this station?
                lat = float(station.find('lat').text)
                lon = float(station.find('lon').text)

                # Is this the station nearby?
                dist = self.haversine(myLat, myLon, lat, lon)
                if (dist < distance):

                    distance = dist
                    self.stationID = station.get('id')

        # This is the station nearby
        for station in self.tree.iterfind('weergegevens/actueel_weer/weerstations/weerstation[@id=\''+ self.stationID +'\']'):
            Domoticz.Log('Found ' + station.find('stationnaam').text + ' at ' + "{:.1f}".format(distance) + ' km from your home location')
            break

        # Check if location is outside of The Netherlands
        if distance > 100:
            Domoticz.Log("Too far away...")
            Domoticz.Log("This plugin only works for locations within The Netherlands")
            self.stationID = ""

    #
    #
    #

    def needUpdate(self, minutes):

        # Is a weather station found?
        if self.stationID == "":
            return False

        nextUpdate = self.lastUpdate + timedelta(minutes=minutes)
        return datetime.now() > nextUpdate

    #
    # Parse a float and return None if no float is given
    #

    def parseFloatValue(self, s):

        try:
            return float(s)
        except:
            return None

    #
    # Based on https://nl.wikipedia.org/wiki/Gevoelstemperatuur
    #

    def getWindChill(self):

        # Do we have a temperature?
        if self.temperature == None:
            return None

        # Wind chill is only valid for temperatures between -46 C and +10 C
        if self.temperature < -46 or self.temperature > 10:
            return temperature

        # No wind, no wind chill
        if self.windSpeed == None:
            return self.temperature

        # Wind chill is only valid for wind speed between 1.3 m/s and 49 m/s
        if self.windSpeed < 1.3 or self.windSpeed > 49:
            return self.temperature

        # Calculate the wind chill based on the JAG/TI-method
        windChill = 13.12 + (0.6215 * self.temperature) - (13.96 * pow(self.windSpeed, 0.16)) + (0.4867 * self.temperature * pow(self.windSpeed, 0.16))
        return round(windChill, 1)

    #
    # Convert the wind direction to a (English) abbreviation
    #

    def getWindDirectionText(self):

        if self.windDirection == None:
            return ""

        if self.windDirection < 0 or self.windDirection > 360:
            return ""

        if self.windDirection > 348 or  self.windDirection <=  11:
            return "N"
        if self.windDirection >  11 and self.windDirection <=  33:
            return "NNE"
        if self.windDirection >  33 and self.windDirection <=  57:
            return "NE"
        if self.windDirection >  57 and self.windDirection <=  78:
            return "ENE"
        if self.windDirection >  78 and self.windDirection <= 102:
            return "E"
        if self.windDirection > 102 and self.windDirection <= 123:
            return "ESE"
        if self.windDirection > 123 and self.windDirection <= 157:
            return "SE"
        if self.windDirection > 157 and self.windDirection <= 168:
            return "SSE"
        if self.windDirection > 168 and self.windDirection <= 192:
            return "S"
        if self.windDirection > 192 and self.windDirection <= 213:
            return "SSW"
        if self.windDirection > 213 and self.windDirection <= 237:
            return "SW"
        if self.windDirection > 237 and self.windDirection <= 258:
            return "WSW"
        if self.windDirection > 258 and self.windDirection <= 282:
            return "W"
        if self.windDirection > 282 and self.windDirection <= 303:
            return "WNW"
        if self.windDirection > 303 and self.windDirection <= 327:
            return "NW"
        if self.windDirection > 327 and self.windDirection <= 348:
            return "NNW"

        # just in case
        return ""

    #
    # Retrieve all the weather data from the nearby weather station
    #

    def getWeather(self):

        # Is the tree set?
        if self.tree == None:
            return False

        # Was the station set properly?
        if self.stationID == "":
            return False

        # Reset all the weather data
        resetWeatherValues(self)

        # Get the weather information from the station
        for station in self.tree.iterfind('weergegevens/actueel_weer/weerstations/weerstation[@id=\''+ self.stationID +'\']'):

            # regenMMPU
            # luchtvochtigheid
            # luchtdruk
            # zichtmeters
            # zonintensiteitWM2

            #self.observationDate = datetime.strptime(station.find('datum').text, '%m/%d/%Y %H:%M:%S')
            self.temperature = self.parseFloatValue(station.find('temperatuurGC').text)
            self.windSpeed = self.parseFloatValue(station.find('windsnelheidMS').text)
            self.windDirection = self.parseFloatValue(station.find('windrichtingGR').text)
            self.windSpeedGusts = self.parseFloatValue(station.find('windstotenMS').text)

            #Domoticz.Log("Observation: " + str(self.observationDate))
            Domoticz.Log("Temperature: " + str(self.temperature))
            Domoticz.Log("Wind Speed: " + str(self.windSpeed))
            Domoticz.Log("Wind Direction: " + str(self.windDirection))
            Domoticz.Log("Wind DirectionText: " + self.getWindDirectionText())
            Domoticz.Log("Wind Speed Gusts: " + str(self.windSpeedGusts))
            Domoticz.Log("Wind Chill: " + str(self.getWindChill()))

            self.lastUpdate = datetime.now()

            return True

        return False
