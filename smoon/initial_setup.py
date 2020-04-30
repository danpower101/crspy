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
    
    os.mkdir(nld['defaultdir']+"/data/")
    os.mkdir(nld['defaultdir']+"/data/calibration_data/")
    os.mkdir(nld['defaultdir']+"/data/crns_data")
    os.mkdir(nld['defaultdir']+"/data/crns_data/level1")
    os.mkdir(nld['defaultdir']+"/data/crns_data/level2")
    os.mkdir(nld['defaultdir']+"/data/crns_data/raw")
    os.mkdir(nld['defaultdir']+"/data/crns_data/theta")
    os.mkdir(nld['defaultdir']+"/data/crns_data/tidy")
    os.mkdir(nld['defaultdir']+"/data/crns_data/dupe_check")
    os.mkdir(nld['defaultdir']+"/data/era5land")
    os.mkdir(nld['defaultdir']+"/data/global_biomass_tiff")
    os.mkdir(nld['defaultdir']+"/data/n0_calibration")
    os.mkdir(nld['defaultdir']+"/data/qa")

    columns_names = ["COUNTRY", "SITENUM", "SITENAME", "INSTALL_DATE", "LOC_LAT", "LOC_LON", "ELEV", "TIMEZONE", "GV", "MEAN_PRESS", "LW",
                    "SOC", "MAX_COUNT", "BD", "CALIB", "NEW_N0", "AGBWEIGHT", "BETA_COEFF", "RAIN_DATA", "TEM_DATA"
                    ]
    
    meta = pd.DataFrame(columns = columns_names)

    meta.to_csv(nld['defaultdir']+"/data/meta_data.csv", header=True, index=False, mode="w") 