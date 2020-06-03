# -*- coding: utf-8 -*-
"""
Created on Mon May 18 11:12:09 2020

@author: Daniel Power
"""

import requests
import smoon
from name_list import nld
import xarray as xr
import pandas as pd
import cdsapi
import os
os.chdir(nld['defaultdir'])
import zipfile

def isric_variables(lat, lon):
    """
    Collects all variables from ISRIC for given lat and lon.
    
    Parameters:
        lat = latitude (degrees)
        lon = longitude (degrees)
    """
    rest_url = "https://rest.isric.org"
    prop_query_url = f"{rest_url}/soilgrids/v2.0/properties/query"
    siteloc={"lat":lat,"lon":lon}
    
    props = {"property":["bdod", "cec", "cfvo", "clay", "nitrogen", "ocd", "ocs", "phh2o", "sand", "silt", "soc"]}
    depths = {"depth":["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm"]}
    values = {"value":["mean", "uncertainty"]}
    
    
    reqprop = requests.get(prop_query_url,params={**siteloc, **props, **depths, **values})
    resdict = reqprop.json()
    return resdict

def isric_depth_mean(resdict, variable):
    """
    Returns mean value
    
    Parameters:
        resdict = dictionary output of isric_variables func
        variable = integer
    
    0=bdod
    1=cec
    2=cfvo
    3=clay
    4=nitrogen
    5=ocd
    6=phh20
    7=sand
    8=silt
    9=soc
    
    """
    tmp=0
    for i in range(len(resdict["properties"]["layers"][variable]["depths"])):    
        tmp += resdict["properties"]["layers"][variable]["depths"][i]["values"]["mean"]
    tmp = tmp/len(resdict["properties"]["layers"][variable]["depths"]) # average
    return tmp

def isric_depth_uc(resdict, variable):
    """
    Returns mean uncertainty.
    
    Parameters:
        resdict = dictionary output of isric_variables func
        variable = integer
    
    0=bdod
    1=cec
    2=cfvo
    3=clay
    4=nitrogen
    5=ocd
    6=phh20
    7=sand
    8=silt
    9=soc
    
    """
    tmp=0
    for i in range(len(resdict["properties"]["layers"][variable]["depths"])):    
        tmp += resdict["properties"]["layers"][variable]["depths"][i]["values"]["uncertainty"]
    tmp = tmp/len(resdict["properties"]["layers"][variable]["depths"]) # average
    return tmp

def isric_wrb_class(lat, lon):
    """
    Returns most probable wrb soil class from ISRIC soilgrid
    
    Parameters:
        lat = latitude (degrees)
        lon = longitude (degrees)
    """
    siteloc={"lat":lat,"lon":lon}
    rest_url = "https://rest.isric.org"
    
    
    #Classification query
    class_query_url = f"{rest_url}/soilgrids/v2.0/classification/query"
    numberclass = {"number_classes":1}
    
    reqclass = requests.get(class_query_url, params = {**siteloc, **numberclass})
    classdict = reqclass.json()
    wrb_class = classdict["wrb_class_name"]
    return wrb_class


def soil_texture(sand, silt, clay):
    """
    Gives soil texture based on decimal percentage of sand, silt and clay.
    Based on USDA soil textures
    
    Parameters:
        sand = percent of sand in soil sample (decimal)
        silt = percent of silt in soil sample (decimal)
        clay = percent of clay in soil sample (decimal) 
    """
    texture = []
    if (sand > 1) or (silt > 1) or (clay > 1):
        raise Exception("Units should be decimal percent e.g. 80% == 0.8")
    
    if (sand <=0.2) & (silt >= 0.8) & (clay <= 0.12):
        texture = "silt"
    elif (sand <=0.45) & (silt <= 0.45) & (clay >= 0.4):
        texture = "clay"    
    elif (sand >= 0.85) & (silt <= 0.15) & (clay <= 0.1):
        texture = "sand"
    elif (0.7 <= sand <= 0.9) & (silt <= 0.3) & (clay <= 0.15):
        texture = "loamy_sand"          
    elif (0.43 <= sand <= 0.85) & (silt <= 0.5) & (clay <= 0.2):
        texture = "sandy_loam"            
    elif (0.45 <= sand <= 0.8) & (silt <= 0.28) & (0.2 <= clay <= 0.35):
        texture = "sandy_clay_loam"          
    elif (0.45 <= sand <= 0.65) & (silt <= 0.2) & (0.35 <= clay <= 0.55):
        texture = "sandy_clay"          
    elif (0.2 <= sand <= 0.45) & (0.15 <= silt <= 0.53) & (0.27 <= clay <= 0.4):
        texture = "clay_loam"           
    elif (0.23 <= sand <= 0.52) & (0.28 <= silt <= 0.5) & (0.07 <= clay <= 0.27):
        texture = "loam"        
    elif (sand <=0.5) & (0.5 <= silt <= 0.88) & (clay <= 0.27):
        texture = "silt_loam"                
    elif (sand <=0.2) & (0.4 <= silt <= 0.73) & (0.27 <= clay <= 0.4):
        texture = "silty_clay_loam"        
    elif (sand <=0.2) & (0.4 <= silt <= 0.6) & (0.4 <= clay <= 0.6):
        texture = "silty_clay"          
    
    return texture
    
############# Land Cover Data ###########################

def dl_land_cover():
    """
    Downloads the 2018 global land cover dataset from the cdsapi:
        
    """
    c = cdsapi.Client()
    savezip = nld['defaultdir']+'/data/land_cover_data/land_cover.zip'
    extractzip = nld['defaultdir']+'/data/land_cover_data/'
    
    c.retrieve(
        'satellite-land-cover',
        {
            'variable': 'all',
            'format': 'zip',
            'year': '2018',
            'version': 'v2.1.1',
        },
        nld['defaultdir']+'/data/land_cover_data/land_cover.zip')
    #extract zip
    print("Extracting zip file and deleting zip...")
    with zipfile.ZipFile(savezip, 'r') as zip_ref:
        zip_ref.extractall(extractzip)
    #remove zip for clean folder
    os.remove(nld['defaultdir']+'/data/land_cover_data/land_cover.zip')
    print("Done")

    
def meta_find_lc(lat, lon):
    landdat = smoon.getlistoffiles(nld['defaultdir'] + "/data/land_cover_data/")
    
    #Open file
    tmp = xr.open_dataset(landdat[0])
    
    #Create value dict
    meanings = tmp.lccs_class.flag_meanings
    meanings = pd.Series(meanings.split())
    meannums = pd.Series(tmp.lccs_class.flag_values)
    ludict = dict(zip(meannums,meanings))
    
    #Find value
    tmp2 = tmp.lccs_class.sel(lat=lat, lon=lon, method='nearest').values[0]
    lc = ludict[tmp2]
    return lc