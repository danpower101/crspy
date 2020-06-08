# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 12:28:55 2020

@author: Daniel Power - University of Bristol
@email: daniel.power@bristol.ac.uk

This package will initialise the file structure in the working directory.
"""

import os
import pandas as pd
from name_list import nld

def initial():
    """
    Build the file structure in the working directory.
    
    Parameters:
        wd = string - working directory path
    """
    try:
        os.mkdir(nld['defaultdir']+"/data/")
    except:
        print("Folder already exists, skipping.")
        pass
    try:
        os.mkdir(nld['defaultdir']+"/data/calibration_data/")
    except:
        print("Folder already exists, skipping.")
        pass
	
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data/level1")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:	
        os.mkdir(nld['defaultdir']+"/data/crns_data/final")
    except:
        print("Folder already exists, skipping.")
        pass
	
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data/simple")
    except:
        print("Folder already exists, skipping.")
        pass
	
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data/raw")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:	
        os.mkdir(nld['defaultdir']+"/data/crns_data/theta")
    except:
        print("Folder already exists, skipping.")
        pass
	
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data/tidy")
    except:
        print("Folder already exists, skipping.")
        pass
    
    try:
        os.mkdir(nld['defaultdir']+"/data/crns_data/dupe_check")
    except:
        print("Folder already exists, skipping.")
        pass
	
    try:
        os.mkdir(nld['defaultdir']+"/data/era5land")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:	
        os.mkdir(nld['defaultdir']+"/data/global_biomass_tiff")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:	
        os.mkdir(nld['defaultdir']+"/data/n0_calibration")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:
        os.mkdir(nld['defaultdir']+"/data/qa")
    except:
        print("Folder already exists, skipping.")
        pass
		
    try:
        os.mkdir(nld['defaultdir']+"/data/land_cover_data")
    except:
        print("Folder already exists, skipping.")
        pass
		
    columns_names = ["COUNTRY", "SITENUM", "SITENAME", "INSTALL_DATE", "LOC_LAT", "LOC_LON", "ELEV", "TIMEZONE", "GV", "MEAN_PRESS", "LW",
                    "SOC", "BD", "CALIB", "NEW_N0", "AGBWEIGHT", "BETA_COEFF", "RAIN_DATA_SOURCE", "TEM_DATA_SOURCE"
                    ]
    # Write metadata file structure if not already there.
    pathfile = nld['defaultdir']+"/data/meta_data.csv"
    files_present = os.path.isfile(pathfile) 
    if not files_present:
        meta = pd.DataFrame(columns = columns_names)
        meta.to_csv(nld['defaultdir']+"/data/meta_data.csv", header=True, index=False, mode="w")
    else:
        print("Meta data file already present")