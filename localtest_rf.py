#!/usr/bin/python3
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
from rainforecast import RainForecast

timeframe = 30
# Den Haag
lat_dh = 52.095556
lon_dh = 4.316389
# Maastricht
lat_mt = 50.849722
lon_mt = 5.693056
# Schiermonnikoog
lat_so = 53.489167
lon_so = 6.202222
# Cadzand (Zeeuws Vlaanderen)
lat_cd = 51.367778
lon_cd = 3.408056
# Berlijn
lat_be = 52.516667
lon_be = 13.416667

rf = RainForecast(lat_dh, lon_dh, timeframe)

testFile = './raintext_remove.txt'

if os.path.isfile(testFile):
    print('File found', testFile)
    result = rf.get_precipfc_data(file = testFile)
    print(result['average'], result['averagemm'])
else:
    print('File', testFile, 'not found')
    result = rf.get_precipfc_data()
    print(result['average'], result['averagemm'])
