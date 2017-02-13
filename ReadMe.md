Domoticz Buienradar.nl Weather Lookup Plugin
============================================


Short summary
-------------

This is a virtual hardware plugin to add weather information from [Buienradar.nl](https://www.buienradar.nl/)
to your Domoticz interface.

It gets the xml weather feed from http://xml.buienradar.nl, finds the
weather station nearby your location and add the relevant weather information
to your Domoticz interface.

Since it uses buienradar.nl it only works for locations in The Netherlands.


Why yet another weather plugin?
-------------------------------

**Q:** Why did I spend a couple of evenings to write this plugin when I could
have spend just a couple of minutes to set up the existing Weather Underground
or AccuWeather plugin?

**A:** Because I can, because it is much easier for Dutch users (no need to setup or
register an API key, etc), because I want to learn how to extend my Domoticz,
because I want to learn Python, because it is fun.


Installation and setup
----------------------

If you are use a Raspberry Pi to host your Domoticz, you probably need to
install libpython3.4 for plugins to work.

```bash
sudo apt install libpython3.4
```

In your `domoticz/plugins` directory do

```bash
git clone https://github.com/ffes/domoticz-buienradar
```

Restart your Domoticz service with:

```bash
sudo service domoticz.sh restart
```

Now go to **Setup**, **Hardware** in your Domoticz interface. There you add
"Buienradar.nl (Weather lookup)".

Enter the latitude and longitude for your location. I hope there is a decent
way to get this information from your Domoticz settings, but I haven't found
it yet.

In the log you should see the plugin coming to life, picking the weather
station nearby and adding "Temperature" information to your interface.


What works?
-----------

At the moment only the temperature is shown in the interface. Other weather
data is shown in the log, but not yet added to the interface.


Developing the plugin
---------------------

To local test there is a `localtest.py` script that can be run from the
command line.

```bash
python3 localtest.py
```

There is also a very small module named `fakeDomoticz.py`. It is used so
localtest.py can use `Domoticz.Log()` and `Domoticz.Debug()`. The output is
simply printed to the console.

To do a real local test download the xml once with

```bash
wget http://xml.buienradar.nl -O buienradar.xml
```

`localtest.py` will use this file when it is found in the current directory.
This way you can avoid hammering the website when testing.

If you want to summit a pull request, please use an editor that supports
[EditorConfig](http://editorconfig.org) so the line endings and indent style
remain consistent.
