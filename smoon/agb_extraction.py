# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 15:43:45 2020

@author: vq18508

This function will extract the relevant information required for above ground biomass.

Data has been obtained from "https://data.globalforestwatch.org/datasets/aboveground-live-woody-biomass-density".




"""
from name_list import nld
import os
os.chdir(nld['defaultdir'])
import rasterio
import itertools
import math
import pandas as pd
import statistics

def rounduplat(x):
    """
    Method to round the latitude to values matching those from globalforestwatch data.
    
    Parameters:
        x = latitude in degrees
    """
    return int(math.ceil(x / 10.0)) * 10
def rounduplon(x):
    """
    Method to round the longitude to values matching those from globalforestwatch data.
    
    Parameters:
        x = longitude in degrees
    """
    return abs(int(math.floor(x / 10.0)) * 10)

def agbextract(write):
    """
    Global forest watch data (see documentation) can be used to provide estimates of above ground biomass.
    Once the data has been manually obtained this code will use meta_data.csv to identify the relevant 
    agb estimates and write them into the metadata file.
    
    
    Parameters:
        
        write = Boolean to identify whether meta_data.csv should be overwritten with data obtained.
            e.g. True
    
    """

    meta = pd.read_csv(nld['defaultdir']+"/data/meta_data.csv")
    
    
    for i in range(len(meta['LOC_LAT'])):
        lat = meta.loc[i, ('LOC_LAT')]
        lon = meta.loc[i, ('LOC_LON')]
        
        # Need below code to adjust for north and south hemispheres.
        if (lat+lat) > lat:
            northing = str(rounduplat(lat))
            northingdir = "N"
        else:
            northing = str(rounduplon(lat)-10) # Minus 10 to do with how files are named on site
            northingdir = "S"   
        if (lon+lon) < lon:
            westing = "{:03d}".format(rounduplon(lon))     # Needs leading zeros
            if westing == "000":
                westingdir = "E"
            else:
                westingdir = "W"       
        else:
            westing = "{:03d}".format(rounduplon(lon))
            westingdir = "E"
              
        """
        Import dataset - extract the band of values interested in. Get the index of the
        coords for the CRNS. 
        """
        dataset = rasterio.open(nld['defaultdir']+nld['rasterdir']+ northing + northingdir+ '_' +westing+ westingdir+ '_t_aboveground_biomass_ha_2000.tif')
        theband = dataset.read(1) # Only one band in this tiff so assign to 1
        indycoord = dataset.index(lon, lat) 
        
        """
        Get a list of all permutations of coords. This is based on the 30m resolution
        and the fact the footprint is approx 400m. This means 7 grid points either way
        as an approximation of the footprint.
        """
        list1 = range((indycoord[0]-7) , indycoord[0]+7)   # Change to 4/5
        list1 = list(list1)
        list2 = range((indycoord[1]-7) , indycoord[1]+7)
        list2 = list(list2)
        allcoords = list(itertools.product(list1, list2))
        
        """
        Extract values for every coordinate and provide the mean.
        
        NOTE: Could change to weighted average of some kind, although this weighting would
              be set on a guess. 
              
        10 megagrams per hectare to kg per (meter squared) = 1 kg per (meter squared) 
        
        Therefore divide mean by 10 to give kg m^2
        
        """
        agball = []
        for coord in allcoords:
            agball.append(theband[coord])
            
        mean = statistics.mean(agball) / 10
        mean = mean/2
        print(meta.loc[i, "SITE_NAME"] + "  -  " + str(mean))
        
        meta.loc[i, ('AGBWEIGHT')] = mean
    if write:
        meta.to_csv(nld['defaultdir'] + "/data/meta_data.csv", header=True, index=False, mode='w')
        return meta
    else:
        return meta
    