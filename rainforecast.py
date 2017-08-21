#
# Rain forecast from Buienradar data
# https://www.buienradar.nl/overbuienradar/gratis-weerdata
# Shows average rainfall for the next minutes
# Author: Gerard - https://github.com/seventer/raintocome
# Updates: G3rard, August 2017, with input from https://github.com/mjj4791/python-buienradar/blob/master/buienradar/buienradar.py

try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

import math
import urllib.request

class RainForecast:

    def __init__(self, latitude=52.101547, longitude=5.177919, timeframe=30):
        self.rainFile = None
        self.url = None
        self.urlbackup = None
        self._lat = latitude
        self._lon = longitude
        self._timeframe = timeframe
        # keys in forcasted precipitation data
        self.AVERAGE = 'average'
        self.AVERAGEMM = 'averagemm'
        self.TIMEFRAME = 'timeframe'
        self.TOTAL = 'total'

    def get_rain(self, file=''):
        """Get the forecasted precipitation data."""

        Domoticz.Debug("Rain forecast started with following coordinates from Domoticz: " + str(self._lat) + ";" + str(self._lon))

        if file != '':
            with open(file, 'r') as myfile:
                self.rainFile = myfile.read()
            return self.rainFile

        # https://br-gpsgadget-new.azurewebsites.net/data/raintext?lat=51&lon=3
        self.url = "https://gps.buienradar.nl/getrr.php?lat={}&lon={}".format(round(float(self._lat),2), round(float(self._lon),2))
        Domoticz.Debug("Rain forecast url: " + self.url)
        self.urlbackup = "http://gadgets.buienradar.nl/data/raintext?lat={}&lon={}".format(round(float(self._lat),2), round(float(self._lon),2))
        try:
            request = urllib.request.Request(self.url)
            with urllib.request.urlopen(request) as response:
                self.rainFile = response.read().decode('utf-8')
            return self.rainFile
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            Domoticz.Error("HTTP error in rain predictor: " + str(e) + " URL: " + self.url)
            Domoticz.Log("Going to try another Buienradar URL")
            try:
                request = urllib.request.Request(self.urlbackup)
                with urllib.request.urlopen(request) as response:
                    self.rainFile = response.read().decode('utf-8')
                return self.rainFile
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                Domoticz.Error("HTTP error in rain predictor: " + str(e) + " URL: " + self.urlbackup)
                return

    def parse_precipfc_data(self):
        """Parse the forecasted precipitation data."""

        # Is the data available?
        if self.rainFile == None:
            Domoticz.Error("No correct data found from Buienradar site")
            return 0, 0.0

        result = {self.AVERAGE: None, self.AVERAGEMM: None, self.TOTAL: None, self.TIMEFRAME: None}

        totalrain = totalrainmm = numberoflines = 0
        lines = self.rainFile.splitlines()
        index = 0
        nrlines = min(len(lines), round(float(self._timeframe)/5) + 1)
        Domoticz.Debug("Timeframe: " + str(self._timeframe) + ", rows: " + str(nrlines))
        while index < nrlines:
            line = lines[index]
            (val, key) = line.split("|")
            rainforecast = int(val)
            mmu = 10**(float((int(val) - 109))/32)
            totalrain += rainforecast
            totalrainmm += float(mmu)
            numberoflines += 1
            index += 1
            Domoticz.Debug(str(val) + '|' + str(key))

        if numberoflines > 0:
            result[self.AVERAGE] = math.ceil(totalrain / numberoflines)
            result[self.AVERAGEMM] = round((totalrainmm / numberoflines), 2)
        else:
            Domoticz.Log("No data found from: " + self.url)
            result[self.AVERAGE] = 0
            result[self.AVERAGEMM] = 0.0
        result[self.TOTAL] = round(totalrainmm/12, 2)
        result[self.TIMEFRAME] = self._timeframe

        #return result
        #Domoticz.Debug('Average: ' + str(result[self.AVERAGE]) + ' | Average mm/h: ' + str(result[self.AVERAGEMM]) + ' | Total: ' + str(result[self.TOTAL]) + ' | Timeframe: ' + str(result[self.TIMEFRAME]))
        Domoticz.Log("Rain forecast: " + str(result[self.AVERAGE]) + " [0-255] | " + str(result[self.AVERAGEMM]) + " mm/hour")
        return result

    def get_precipfc_data(self, file=''):
        self.get_rain(file)
        return self.parse_precipfc_data()
