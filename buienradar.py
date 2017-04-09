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
        self.resetWeatherValues()

    def resetWeatherValues(self):

        self.observationDate = datetime.now()
        self.temperature = None             # degrees Celsius
        self.windSpeed = None               # m/s
        self.windBearing = None             # degrees
        self.windSpeedGusts = None          # m/s
        self.pressure = None                # hPa
        self.humidity = None                # percentage

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
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            Domoticz.Log("HTTP error: " + str(e) + " URL: " + url)
            return

        try:
             self.tree = ET.parse(xml)
        except ET.ParseError as err:
             Domoticz.Log("XML parsing error: " + err)
             return

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
    # Parse an int and return None if no int is given
    #

    def parseIntValue(self, s):

        try:
            return int(s)
        except:
            return None

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
            return self.temperature

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

    def getWindDirection(self):

        if self.windBearing == None:
            return ""

        if self.windBearing < 0 or self.windBearing > 360:
            return ""

        if self.windBearing > 348 or  self.windBearing <=  11:
            return "N"
        if self.windBearing >  11 and self.windBearing <=  33:
            return "NNE"
        if self.windBearing >  33 and self.windBearing <=  57:
            return "NE"
        if self.windBearing >  57 and self.windBearing <=  78:
            return "ENE"
        if self.windBearing >  78 and self.windBearing <= 102:
            return "E"
        if self.windBearing > 102 and self.windBearing <= 123:
            return "ESE"
        if self.windBearing > 123 and self.windBearing <= 157:
            return "SE"
        if self.windBearing > 157 and self.windBearing <= 168:
            return "SSE"
        if self.windBearing > 168 and self.windBearing <= 192:
            return "S"
        if self.windBearing > 192 and self.windBearing <= 213:
            return "SSW"
        if self.windBearing > 213 and self.windBearing <= 237:
            return "SW"
        if self.windBearing > 237 and self.windBearing <= 258:
            return "WSW"
        if self.windBearing > 258 and self.windBearing <= 282:
            return "W"
        if self.windBearing > 282 and self.windBearing <= 303:
            return "WNW"
        if self.windBearing > 303 and self.windBearing <= 327:
            return "NW"
        if self.windBearing > 327 and self.windBearing <= 348:
            return "NNW"

        # just in case
        return ""

    #
    # Based on various picture of analogue barometers found in the Internet
    # If anybody has better input, please let me know
    #

    def getBarometerForecast(self):

        if self.pressure == None:
            return 5

        # Thunderstorm = 4
        if self.pressure < 966:
            return 4

        # Cloudy/Rain = 6
        if self.pressure < 993:
            return 6

        # Cloudy = 2
        if self.pressure < 1007:
            return 2

        # Unstable = 3
        if self.pressure < 1013:
            return 3

        # Stable = 0
        if self.pressure < 1033:
            return 0

        # Sunny = 1
        return 1

    #
    # Based on Mollier diagram and Fanger (comfortable)
    # These values are normally used for indoor situation,
    # but this weather lookup plugin obviously is outdoor.
    #

    def getHumidityStatus(self):

        # Is there a humidity?
        if self.humidity == None:
            return 0

        # Dry?
        if self.humidity <= 30:
            return 2

        # Wet?
        if self.humidity >= 70:
            return 3

        # Comfortable?
        if self.humidity >= 35 and self.humidity <= 65:
            if self.temperature != None:
                if self.temperature >= 22 and self.temperature <= 26:
                    return 1

        # Normal
        return 0

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
        self.resetWeatherValues()

        # Get the weather information from the station
        for station in self.tree.iterfind('weergegevens/actueel_weer/weerstations/weerstation[@id=\''+ self.stationID +'\']'):

            # regenMMPU
            # zichtmeters
            # zonintensiteitWM2

            #self.observationDate = datetime.strptime(station.find('datum').text, '%m/%d/%Y %H:%M:%S')
            self.temperature = self.parseFloatValue(station.find('temperatuurGC').text)
            self.windSpeed = self.parseFloatValue(station.find('windsnelheidMS').text)
            self.windBearing = self.parseFloatValue(station.find('windrichtingGR').text)
            self.windSpeedGusts = self.parseFloatValue(station.find('windstotenMS').text)
            self.pressure = self.parseFloatValue(station.find('luchtdruk').text)
            self.humidity = self.parseIntValue(station.find('luchtvochtigheid').text)

            #Domoticz.Log("Observation: " + str(self.observationDate))
            Domoticz.Log("Temperature: " + str(self.temperature))
            Domoticz.Log("Wind Speed: " + str(self.windSpeed))
            Domoticz.Log("Wind Bearing: " + str(self.windBearing))
            Domoticz.Log("Wind Direction: " + self.getWindDirection())
            Domoticz.Log("Wind Speed Gusts: " + str(self.windSpeedGusts))
            Domoticz.Log("Wind Chill: " + str(self.getWindChill()))
            Domoticz.Log("Barometer: " + str(self.pressure))
            Domoticz.Log("Barometer Forecast: " + str(self.getBarometerForecast()))
            Domoticz.Log("Humidity: " + str(self.humidity))
            Domoticz.Log("Humidity status: " + str(self.getHumidityStatus()))

            self.lastUpdate = datetime.now()

            return True

        return False
