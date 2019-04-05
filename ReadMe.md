Domoticz Buienradar.nl Weather Lookup Plugin
============================================


Short summary
-------------

This is a virtual hardware plugin to add weather information from [Buienradar.nl](https://www.buienradar.nl/)
to your [Domoticz](https://www.domoticz.com/) interface.

It gets the xml weather feed from http://xml.buienradar.nl, finds the
weather station nearby your location and add the relevant weather information
to your Domoticz interface.

Since it uses buienradar.nl it only works for locations in The Netherlands.

This plugin is open source and it can be found at https://github.com/ffes/domoticz-buienradar/


Why yet another weather plugin?
-------------------------------

**Q:** Why did I spend a couple of evenings to write this plugin when I could
have spend just a couple of minutes to set up the existing Weather Underground
or AccuWeather plugin?

**A:** Because I can, because it is much easier for Dutch users (no need to setup or
register an API key, etc), because I want to learn how to extend my Domoticz,
because I improve my Python skills, because it is fun.


Installation and setup
----------------------

```bash
cd domoticz/plugins
git clone https://github.com/ffes/domoticz-buienradar.git
```

Restart your Domoticz service with:

```bash
sudo service domoticz.sh restart
```

Now go to **Setup**, **Hardware** in your Domoticz interface. There you add
**Buienradar.nl (Weather lookup)**.

Make sure you enter all the required fields.

In the log you should see the plugin coming to life, picking the weather
station nearby and adding the weather information to your interface.


Known bugs
----------

At the moment there is no way to determine the type of the devices
from within the plugin. So when you want to change any of those
settings you need to remove all the devices and restart Domoticz.
The new devices will be added matching your settings.

Other then that use [GitHub Issues](https://github.com/ffes/domoticz-buienradar/issues)
for feature request or bug reports.


State of development
--------------------

With the current implementation of the Python plugin framework this
plugin is quiet feature complete. Only rain levels could be added.

A useful features in the plugin framework to have would be:
* Get the TypeName of the plugins devices. With that it would be
  possible to determine if new devices need to be created when
  the user changes one of the selections on the hardware page.

Change log
---------------------
### v2.3 2019-02-19
* Better error handling

### v2.2 2019-02-15
* Limit the wheater forecast device to 200 characters

## v2 2019-01-02
* Make use of rain devices instead of general text devices.
* Show warning when location is not set in settings

### v1.1.0, 2017-03-04

* Get the location from the Settings instead of asking the user
  This requires a newly implemented Setting dictionary in the
  Python interface.

### v1.0.1, 2017-02-19

*  Make filling the devices more robust

## v1.0.0, 2017-02-19

* First release

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
