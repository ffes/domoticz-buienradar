#
#   Buienradar.nl Weather Lookup Plugin
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#
#   Frank Fesevur, 2017
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
            print('Retrieve weather data from ' + url)
            xml = urllib.request.urlopen(url, data=None)
        except urllib.error.HTTPError as e:
            print("HTTP error: " + str(e) + " URL: " + url)
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
    # Retrieve all the weather data from the nearby weather station
    #

    def getWeather(self):

        # Is the tree set?
        if self.tree == None:
            return

        # Was the station set properly?
        if self.stationID == "":
            return

        # Get the weather information from the station
        for station in self.tree.iterfind('weergegevens/actueel_weer/weerstations/weerstation[@id=\''+ self.stationID +'\']'):

            # windsnelheidMS
            # windrichtingGR
            # regenMMPU
            # luchtvochtigheid
            # luchtdruk
            # zichtmeters
            # windstotenMS
            # zonintensiteitWM2

            datum = datetime.strptime(station.find('datum').text, '%m/%d/%Y %H:%M:%S')
            temp = station.find('temperatuurGC').text

            Domoticz.Log("Observation: " + str(datum))
            Domoticz.Log("Temparture: " + temp)

            #Domoticz.Devices[1].Update(0, temp)
            return
