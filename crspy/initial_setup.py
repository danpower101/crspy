# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 12:28:55 2020

@author: Daniel Power - University of Bristol
@email: daniel.power@bristol.ac.uk

This package will initialise the file structure in the working directory.
"""

import os
import pandas as pd
from configparser import RawConfigParser

def create_config_file(wd = None):
    config_object = RawConfigParser()
    config_object['config'] = {
        ";Change defaultdir to your working directory":"",
        "defaultdir" : "/home/crspyuser/wd",
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

def initial(wd):
    """
    Build the file structure in the working directory.

    Parameters:
        wd : string 
           working directory path
    """
    try:
        os.mkdir(wd+"/data/")
    except:
        print("Folder already exists, skipping.")
        pass
    try:
        os.mkdir(wd+"/data/calibration_data/")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/level1")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/final")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/simple")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/raw")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/theta")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/tidy")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/crns_data/dupe_check")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/era5land")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/global_biomass_netcdf")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/n0_calibration")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/qa")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/land_cover_data")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/nmdb")
    except:
        print("Folder already exists, skipping.")
        pass

    try:
        os.mkdir(wd+"/data/figures")
    except:
        print("Folder already exists, skipping.")
        pass

    create_config_file()

    columns_names = ["COUNTRY", "SITENUM", "SITENAME", "INSTALL_DATE", "LATITUDE", "LONGITUDE", "ELEV", "TIMEZONE", "GV", "LW", "SOC",
                     "BD", "N0", "AGBWEIGHT",  "RAIN_DATA_SOURCE", "TEM_DATA_SOURCE", "RH_DATA_SOURCE", "BETA_COEFF", "REFERENCE_PRESS"
                     ]
    # Write metadata file structure if not already there.
    pathfile = wd + "/data/metadata.csv"
    files_present = os.path.isfile(pathfile)
    if not files_present:
        meta = pd.DataFrame(columns=columns_names)
        meta.to_csv(wd + "/data/metadata.csv",
                    header=True, index=False, mode="w")
    else:
        print("Meta data file already present")
