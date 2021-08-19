from configparser import RawConfigParser

config_object = RawConfigParser()
config_object['config'] = {
    ";Change defaultdir to your working directory":"",
    "defaultdir" : "/path/to/wd/here",
    "noval" : "-999",
    "era5_filename":"era5land_all",
    "jung_ref":"159",
    "defaultbd":"1.43",
    "cdtformat":"%d/%m/%Y",
    ";accuracy is for n0 calibration":"",
    "accuracy":"0.01",
    ";QA values are percentages (e.g. below 30% N0)":"",
    "belowN0":"30",
    "timestepdiff":"20",
    ";density=density of quartz":"",
    "density":"2.65",
    "smwindow":"12",
    "pv0":"0",
    "a0":"0.0808",
    "a1":"0.372",
    "a2":"0.115"
}


with open('config.ini','w') as conf:
    config_object.write(conf)