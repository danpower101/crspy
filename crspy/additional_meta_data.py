# -*- coding: utf-8 -*-
"""
Created on Mon May 18 11:12:09 2020

@author: Daniel Power
@email: daniel.power@bristol.ac.uk
"""

import requests
import crspy
from name_list import nld
import xarray as xr
import pandas as pd
import cdsapi
import os
os.chdir(nld['defaultdir'])
import zipfile
import urllib
from bs4 import BeautifulSoup

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
    print("Downloading...")
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

    
def find_lc(lat, lon):
    landdat = crspy.getlistoffiles(nld['defaultdir'] + "/data/land_cover_data/")
    
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



####################### AGB data ##############################################
def dl_agb():
    print("Downloading...")
    urllib.request.urlretrieve("ftp://anon-ftp.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/2017/v1.0/netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc", nld['defaultdir']+"/data/global_biomass_netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc" )
    print("Done")
    


def get_agb(lat, lon, tol=0.001):
    ncfile = nld['defaultdir']+"/data/global_biomass_netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc"
    with xr.open_dataset(ncfile) as ds:
        agb = ds.sel(lat=lat, lon=lon, method='nearest', tolerance = tol).agb.values[0] # given in megagrams per hectare
        agb = agb/10 #convert to kg/m2
    return agb
        
        
###################### Fill in metadata ######################################
        
def fill_meta_data(meta):
    
    """
    Reads in meta_data table, uses the latitude and longitude of each site to find
    metadata from the ISRIC soil database, as well as calculating reference pressure
    and beta coefficient.
    
    REQUIRED COLUMNS IN META_DATA:
        LATITUDE: latitude in degrees
            e.g. 51
        LONGITUDE: longitude in degrees
            e.g. 51.1
        ELEV: elevation of site in metres
            e.g. 201
        GV: cutoff rigidity of site (can be obtained at http://crnslab.org/util/rigidity.php )
            e.g. 2.2
    """
    
    meta['SITENUM'] = meta.SITENUM.map("{:03}".format) # Ensure leading zeros
    
    
    for i in range(len(meta['LATITUDE'])):
        print(i)
        
        try:
            lat = meta['LATITUDE'][i]
            lon = meta['LONGITUDE'][i]
            
            
            resdict = crspy.isric_variables(lat, lon)
            wrb = crspy.isric_wrb_class(lat, lon)
            
                    #Bulk Density
            bdod = crspy.isric_depth_mean(resdict, 0)
            bdod = bdod/100 # convert to decimal fraction
            bdoduc = crspy.isric_depth_uc(resdict, 0)
            bdoduc = bdoduc/100
            
            #Cation Exchange Capacity
            cec = crspy.isric_depth_mean(resdict, 1)
            cecuc = crspy.isric_depth_uc(resdict, 1)
        
            # Coarse Fragment Volume
            cfvo = crspy.isric_depth_mean(resdict, 2)
            cfvo = cfvo/10 # convert to decimal fraction
            cfvouc = crspy.isric_depth_uc(resdict, 2)
            cfvouc = cfvouc/10
        
            # Clay as prcnt
            clay = crspy.isric_depth_mean(resdict, 3)
            clay = clay/1000 # convert to decimal fraction
            clayuc = crspy.isric_depth_uc(resdict, 3)
            clayuc = clayuc/1000
        
            # Nitrogen
            nitro = crspy.isric_depth_mean(resdict, 4)
            nitro = nitro/100 # convert to g/kg
            nitrouc = crspy.isric_depth_uc(resdict, 4)
            nitrouc = nitrouc/100
        
            #OCD CURRENTLY DATA APPEARS TO ALWAYS BE NONETYPE - REMOVED
           # ocd = smoon.isric_depth_mean(resdict, 5)
           # ocd = ocd/1000 # convert to kg/dm**3
           # ocduc = smoon.isric_depth_uc(resdict, 5)
           # ocduc = ocduc/1000
        
            #phh20
            phh20 = crspy.isric_depth_mean(resdict, 6)
            phh20 = phh20/10 # convert to pH
            phh20uc = crspy.isric_depth_uc(resdict, 6)
            phh20uc = phh20uc/10
        
            #Sand
            sand = crspy.isric_depth_mean(resdict, 7)
            sand = sand/1000 # convert to decimal fraction
            sanduc = crspy.isric_depth_uc(resdict, 7)
            sanduc = sanduc/1000
        
            #Silt
            silt = crspy.isric_depth_mean(resdict, 8)
            silt = silt/1000 # convert to decimal fraction
            siltuc = crspy.isric_depth_uc(resdict, 8)
            siltuc = siltuc/1000    
            
            #SOC
            soc  = crspy.isric_depth_mean(resdict, 9)
            soc = soc/1000 # convert to decimal fraction
            socuc = crspy.isric_depth_uc(resdict, 9)
            socuc = socuc/1000
            
            meta.at[i, 'BD_ISRIC'] = bdod
            meta.at[i, 'BD_ISRIC_UC'] = bdoduc
            
            meta.at[i, 'SOC_ISRIC'] = soc
            meta.at[i, 'SOC_ISRIC_UC'] = socuc
            
            meta.at[i, 'pH_H20_ISRIC'] = phh20
            meta.at[i, 'pH_H20_ISRIC_UC'] = phh20uc
            
            meta.at[i, 'CEC_ISRIC'] = cec
            meta.at[i, 'CEC_ISRIC_UC'] = cecuc
            
            meta.at[i, 'CFVO_ISRIC'] = cfvo
            meta.at[i, 'CFVO_ISRIC_UC'] = cfvouc
            
            meta.at[i, 'NITROGEN_ISRIC'] = nitro
            meta.at[i, 'NITROGEN_ISRIC_UC'] = nitrouc
            
            meta.at[i, 'SAND_ISRIC'] = sand
            meta.at[i, 'SAND_ISRIC_UC'] = sanduc
            
            meta.at[i, 'SILT_ISRIC'] = silt
            meta.at[i, 'SILT_ISRIC_UC'] = siltuc
            
            meta.at[i, 'CLAY_ISRIC'] = clay
            meta.at[i, 'CLAY_ISRIC_UC'] = clayuc
            
            meta.at[i, 'WRB_ISRIC'] = wrb
            meta.at[i, 'SOIL_TEXTURE'] = crspy.soil_texture(sand, silt, clay)
            
            #ADD LAND COVER
            lc = crspy.find_lc(lat, lon)
            meta.at[i, 'LAND_COVER'] = lc
            
            #Add above ground biomass data
            agb = crspy.get_agb(lat, lon)
            meta.at[i, 'AGBWEIGHT'] = agb
        except:
            pass
        



    print("Calculate Beta Coeff...")

    meta['BETA_COEFF'], meta['REFERENCE_PRESS'] = crspy.betacoeff(meta['LATITUDE'],
        meta['ELEV'], meta['GV'])
    
    meta.to_csv(nld['defaultdir'] + "/data/meta_data.csv", header=True, index=False, mode='w')
    
    return meta


def nmdb_get(startdate, enddate):
    """
    Will collect data for Junfraujoch station that is required to calculate fsol.
    Returns a dictionary that can be used to fill in values to the main dataframe
    of each site.
    
    Parameters:
        startdate = date of the format YYYY-mm-dd
            e.g 2015-10-01
        enddate = date of the format YYYY-mm-dd
            e.g. 2016-10-01
    """
    #split for use in url
    sy,sm,sd = str(startdate).split("-")
    ey,em,ed = str(enddate).split("-")
    
    #Collect html from request and extract table and write to dict
    url = "http://nest.nmdb.eu/draw_graph.php?formchk=1&stations[]=JUNG&tabchoice=1h&dtype=corr_for_efficiency&tresolution=60&force=1&yunits=0&date_choice=bydate&start_day={sd}&start_month={sm}&start_year={sy}&start_hour=0&start_min=0&end_day={ed}&end_month={em}&end_year={ey}&end_hour=23&end_min=59&output=ascii"
    url = url.format(sd=sd, sm=sm, sy=sy, ed=ed, em=em, ey=ey)
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, features="html.parser")
    pre = soup.find_all('pre')
    pre = pre[0].text
    pre = pre[pre.find('start_date_time'):]
    pre = pre.replace("start_date_time   1HCOR_E", "")
    f = open(nld['defaultdir']+"data/nmdb/tmp.txt", "w")
    f.write(pre)
    f.close()
    df = open(nld['defaultdir']+"data/nmdb/tmp.txt", "r")
    lines = df.readlines()
    df.close()
    lines = lines[1:]
    dfneut = pd.DataFrame(lines)
    dfneut = dfneut[0].str.split(";", n = 2, expand = True) 
    cols = ['DATE', 'COUNT']
    dfneut.columns = cols
    dates = pd.to_datetime(dfneut['DATE'])
    count = dfneut['COUNT']
    
    dfdict = dict(zip(dates, count))
    
    return dfdict

