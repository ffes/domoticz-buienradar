#!/usr/bin/env python3
#
#   Buienradar.nl Weather Lookup Plugin
#
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#   About the weather service:
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#

import os
from buienradar import Buienradar

x = Buienradar()

xmlFile = './buienradar.xml'

if os.path.isfile(xmlFile):
    x.getBuienradarXML(file = xmlFile)
else:
    x.getBuienradarXML()

x.getNearbyWeatherStation(52.095556,  4.316389)         # Den Haag
#x.getNearbyWeatherStation(50.849722,  5.693056)         # Maastricht
#x.getNearbyWeatherStation(53.489167,  6.202222)         # Schiermonnikoog
#x.getNearbyWeatherStation(51.367778,  3.408056)         # Cadzand (Zeeuws Vlaanderen)
#x.getNearbyWeatherStation(52.516667, 13.416667)         # Berlijn

x.getWeather()
