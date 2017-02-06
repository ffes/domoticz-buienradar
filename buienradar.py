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

        self.observationDate = None
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
                temp = station.find('temperatuurGC').text

                # If no is temperature set, skip this entry
                # Many weather stations only measure wind speed
                # They are not useful for weather information in domoticz
                if temp == "-":
                    continue

                # Where is this station?
                lat = float(station.find('latGraden').text)
                lon = float(station.find('lonGraden').text)

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
        self.observationDate = None
        self.temperature = None
        self.windSpeed = None
        self.windDirection = None
        self.windSpeedGusts = None

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
            Domoticz.Log("Wind Speed Gusts: " + str(self.windSpeedGusts))

            self.lastUpdate = datetime.now()

            return True

        return False
