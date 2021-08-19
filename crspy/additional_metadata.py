# -*- coding: utf-8 -*-
"""
Created on Mon May 18 11:12:09 2020

@author: Daniel Power
@email: daniel.power@bristol.ac.uk
"""

import requests
import xarray as xr
import pandas as pd
import cdsapi
import os
import zipfile
import urllib
from bs4 import BeautifulSoup
import numpy as np
import math
# crspy funcs
from crspy.gen_funcs import getlistoffiles
from crspy.mass_atten import betacoeff


"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')


def isric_variables(lat, lon):
    """isric_variables collects all variables from ISRIC database for given latitude and longitude.

    Parameters
    ----------
    lat : float
        latitude of site in degrees
    lon : float
        longitude of site in degrees

    Returns
    -------
    dictionary
        dictionary containing all the relevant soil properties data
    """

    rest_url = "https://rest.isric.org"
    prop_query_url = f"{rest_url}/soilgrids/v2.0/properties/query"
    siteloc = {"lat": lat, "lon": lon}

    props = {"property": ["bdod", "cec", "cfvo", "clay",
                          "nitrogen", "ocd", "ocs", "phh2o", "sand", "silt", "soc"]}
    depths = {"depth": ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm"]}
    values = {"value": ["mean", "uncertainty"]}

    reqprop = requests.get(prop_query_url, params={
                           **siteloc, **props, **depths, **values})
    resdict = reqprop.json()
    return resdict


def isric_depth_mean(resdict, variable):
    """isric_depth_mean returns mean values of the collected soil data - equal average

    Parameters
    ----------
    resdict : dictionary
        output from isric_variables function
    variable : int
        number corresponding to the variable to average
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

    Returns
    -------
    float   
        returns the depth averaged value
    """

    tmp = 0
    for i in range(len(resdict["properties"]["layers"][variable]["depths"])):
        tmp += resdict["properties"]["layers"][variable]["depths"][i]["values"]["mean"]
    tmp = tmp/len(resdict["properties"]["layers"]
                  [variable]["depths"])  # average
    return tmp


def isric_depth_uc(resdict, variable):
    """isric_depth_uc returns mean uncertainty values - equal average.

    Parameters
    ----------
    resdict : dictionary 
         output of isric_variables func
    variable : int
        number corresponding to the variable to average
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
    tmp = 0
    for i in range(len(resdict["properties"]["layers"][variable]["depths"])):
        tmp += resdict["properties"]["layers"][variable]["depths"][i]["values"]["uncertainty"]
    tmp = tmp/len(resdict["properties"]["layers"]
                  [variable]["depths"])  # average
    return tmp


def isric_wrb_class(lat, lon):
    """isric_wrb_class returns most probable wrb soil class from ISRIC soilgrid

    Parameters
    ----------
    lat : float
        latitude of site (degrees)
    lon : float
        longitude of site (degrees)

    Returns
    -------
    string
        the highest probability WRB as defined by the ISRIC soilgridsv2 database
    """

    siteloc = {"lat": lat, "lon": lon}
    rest_url = "https://rest.isric.org"

    # Classification query
    class_query_url = f"{rest_url}/soilgrids/v2.0/classification/query"
    numberclass = {"number_classes": 1}

    reqclass = requests.get(class_query_url, params={**siteloc, **numberclass})
    classdict = reqclass.json()
    wrb_class = classdict["wrb_class_name"]
    return wrb_class


def soil_texture(sand, silt, clay):
    """soil_texture gives soil texture based on decimal percentage of sand, silt and clay.
    Based on USDA soil textures

    Parameters
    ----------
    sand : float
        percentage of sand given as a decimal between 0 and 1
    silt : float
        percentage of silt given as a decimal between 0 and 1
    clay : float
        percentage of clay given as a decimal between 0 and 1

    Returns
    -------
    string
        returns the USDA soil type

    Raises
    ------
    Exception
        Check that the units are given as decimal rather than percentage
    """

    texture = []
    if (sand > 1) or (silt > 1) or (clay > 1):
        raise Exception("Units should be decimal percent e.g. 80% == 0.8")

    if (sand <= 0.2) & (silt >= 0.8) & (clay <= 0.12):
        texture = "silt"
    elif (sand <= 0.45) & (silt <= 0.45) & (clay >= 0.4):
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
    elif (sand <= 0.5) & (0.5 <= silt <= 0.88) & (clay <= 0.27):
        texture = "silt_loam"
    elif (sand <= 0.2) & (0.4 <= silt <= 0.73) & (0.27 <= clay <= 0.4):
        texture = "silty_clay_loam"
    elif (sand <= 0.2) & (0.4 <= silt <= 0.6) & (0.4 <= clay <= 0.6):
        texture = "silty_clay"

    return texture

############# Land Cover Data ###########################


def dl_land_cover(nld=nld):
    """
    Downloads the 2018 global land cover dataset from the cdsapi:

    Parameters
    ----------

    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']
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
    # extract zip
    print("Extracting zip file and deleting zip...")
    with zipfile.ZipFile(savezip, 'r') as zip_ref:
        zip_ref.extractall(extractzip)
    # remove zip for clean folder
    os.remove(nld['defaultdir']+'/data/land_cover_data/land_cover.zip')
    print("Done")


def find_lc(lat, lon, nld=nld):
    """find_lc uses latitude and longitude to extract land cover data from the ESA_CCI data.

    Parameters
    ----------
    lat : float
        latitude of the site (degrees)
    lon : float
        longitude of the site (degrees)
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    string
        land cover value from the grid
    """
    nld=nld['config'] 
    landdat = getlistoffiles(nld['defaultdir'] + "/data/land_cover_data/")

    # Open file
    tmp = xr.open_dataset(landdat[0])

    # Create value dict
    meanings = tmp.lccs_class.flag_meanings
    meanings = pd.Series(meanings.split())
    meannums = pd.Series(tmp.lccs_class.flag_values)
    ludict = dict(zip(meannums, meanings))

    # Find value
    tmp2 = tmp.lccs_class.sel(lat=lat, lon=lon, method='nearest').values[0]
    lc = ludict[tmp2]
    return lc


####################### AGB data ##############################################
def dl_agb(nld=nld):
    """
    Downloads the above ground biomass dataset from the ESA-CCI database and stores in data.

    Parameters
    ----------
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    print("Downloading...")
    urllib.request.urlretrieve("ftp://anon-ftp.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/2017/v1.0/netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc",
                               nld['defaultdir']+"/data/global_biomass_netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc")
    print("Done")


def get_agb(lat, lon, tol=0.001, nld=nld):
    """get_agb uses latitude and longitude to extract the above ground biomass data from the ESA_CCI dataset

    Parameters
    ----------
    lat : float
        latitude of site (degrees)
    lon : float
        longitude of site (degrees)
    tol : float, optional
        tolerance for finding nearest grid point, by default 0.001
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    float
        above ground biomass value in kg/m2
    """
    nld=nld['config']
    ncfile = nld['defaultdir'] + \
        "/data/global_biomass_netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc"
    with xr.open_dataset(ncfile) as ds:
        # given in megagrams per hectare
        agb = ds.sel(lat=lat, lon=lon, method='nearest',
                     tolerance=tol).agb.values[0]
        agb = agb/10  # convert to kg/m2
    return agb

############################## Get Jungfraujoch Data ##########################


def nmdb_get(startdate, enddate, station="JUNG", nld=nld):
    """nmdb_get will collect data for Junfraujoch station that is required to calculate fsol.
    Returns a dictionary that can be used to fill in values to the main dataframe
    of each site.

    Parameters
    ----------
    startdate : datetime
        start date of desire data in format YYYY-mm-dd
            e.g 2015-10-01
    enddate : datetime
        end date of desired data in format YYY-mm-dd
    station : str, optional
        if using different station provide the value here (NMDB.eu shows alternatives), by default "JUNG"
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    dict
        dictionary of neutron count data from NMDB.eu
    """
    nld = nld['config']
    # split for use in url
    sy, sm, sd = str(startdate).split("-")
    ey, em, ed = str(enddate).split("-")

    # Collect html from request and extract table and write to dict
    url = "http://nest.nmdb.eu/draw_graph.php?formchk=1&stations[]={station}&tabchoice=1h&dtype=corr_for_efficiency&tresolution=60&force=1&yunits=0&date_choice=bydate&start_day={sd}&start_month={sm}&start_year={sy}&start_hour=0&start_min=0&end_day={ed}&end_month={em}&end_year={ey}&end_hour=23&end_min=59&output=ascii"
    url = url.format(station=station, sd=sd, sm=sm, sy=sy, ed=ed, em=em, ey=ey)
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, features="html.parser")
    pre = soup.find_all('pre')
    pre = pre[0].text
    pre = pre[pre.find('start_date_time'):]
    pre = pre.replace("start_date_time   1HCOR_E", "")
    f = open(nld['defaultdir']+"/data/nmdb/tmp.txt", "w")
    f.write(pre)
    f.close()
    df = open(nld['defaultdir']+"/data/nmdb/tmp.txt", "r")
    lines = df.readlines()
    df.close()
    lines = lines[1:]
    dfneut = pd.DataFrame(lines)
    dfneut = dfneut[0].str.split(";", n=2, expand=True)
    cols = ['DATE', 'COUNT']
    dfneut.columns = cols
    dates = pd.to_datetime(dfneut['DATE'])
    count = dfneut['COUNT']

    dfdict = dict(zip(dates, count))

    return dfdict


def nmdb_get_alt(startdate, enddate, nld=nld):
    """nmdb_get_alt alternative to the above nmdb_get which will use a recorded file saved in the folder
    This is brought in to deal with when nmdb may be down

    Parameters
    ----------
    startdate : datetime
        start date of desire data in format YYYY-mm-dd
            e.g 2015-10-01
    enddate : datetime
        end date of desired data in format YYY-mm-dd
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    dict
        dictionary of neutron count data from NMDB.eu
    """
    nld=nld['config']
    df = open(nld['defaultdir']+"/data/nmdb/tmp.txt", "r")
    lines = df.readlines()
    df.close()
    lines = lines[1:]
    dfneut = pd.DataFrame(lines)
    dfneut = dfneut[0].str.split(";", n=2, expand=True)
    cols = ['DATE', 'COUNT']
    dfneut.columns = cols

    dfneut['DATE'] = pd.to_datetime(dfneut['DATE'])

    dates = dfneut['DATE']
    count = dfneut['COUNT']

    dfdict = dict(zip(dates, count))

    return dfdict


############## Koppen Gieger classification ###################################
"""
Based off the paper Peel et al., (2007) https://hess.copernicus.org/articles/11/1633/2007/hess-11-1633-2007.pdf

Uses the ERA5_Land data for each site to give a KG class.

"""


def KG_func(meta, country, sitenum, nld=nld):
    """KG_func - Takes in the metadata along with a country/sitenum. Will then check to see if local data is available. If it is, it will calculate Koppen-Geigger climate classes using local data as well as Mean Annual Precipitation(MAP) and Mean Annual Temperature(MAT).

    Based off the rules in Peel et al., (2007) https://hess.copernicus.org/articles/11/1633/2007/hess-11-1633-2007.pdf

    Parameters
    ----------
    meta : dataframe
        The dataframe of metadata
    country : string
        Country string e.g. "USA"
    sitenum : string
        Site Number string e.g. "011"
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    meta : dataframe
        Returns the metadata dataframe with KG, MAP and MAT values inputted for the site.
    """
    nld=nld['config']
    sitecode = country+"_SITE_"+sitenum
    # CHECK IF LOCAL TEMP AND PRECIP IS AVAILABLE
    dfcheck = nld['defaultdir']+"/data/crns_data/raw/"+str(sitecode)+".txt"
    try:
        dfcheck = pd.read_csv(dfcheck, sep="\t")
    except:
        print("No raw data to check... moving along!")
        # Introduced as if no data currently availabel it will crash (still may want to check on info)
        dfcheck = pd.DataFrame()
        dfcheck['E_TEM'] = 1

    # Arbitary amount to check if there are values attached in E_TEM
    if len(dfcheck['E_TEM'].unique()) > 5:

        df = pd.DataFrame()
        df['DT'] = pd.to_datetime(dfcheck['TIME'])
        df['TEMP'] = dfcheck['E_TEM']
        df['PRCP'] = dfcheck['RAIN']  # !!! Change to 'PRECIP'
        df['YEAR'] = df['DT'].dt.year
        df['MONTH'] = df['DT'].dt.month
        df['HOUR'] = df['DT'].dt.hour

        # Need to do mastertime process as data is raw
        df['DT'] = df.DT.dt.floor(freq='H')
        dtcol = df['DT']
        df.drop(labels=['DT'], axis=1, inplace=True)  # Move DT to first col
        df.insert(0, 'DT', dtcol)
        df = df.set_index(df.DT)
        df['dupes'] = df.duplicated(subset="DT")
        df = df.drop(df[df.dupes == True].index)
        idx = pd.date_range(
            df.DT.iloc[0], df.DT.iloc[-1], freq='1H', closed='left')
        df = df.reindex(idx, fill_value=nld['noval'])
        df['DT'] = df.index
        df = df.replace(int(nld['noval']), np.nan)

    else:

        era5 = xr.open_dataset(
            nld['defaultdir']+"data/era5land/"+nld['era5_filename']+".nc")
        try:
            era5site = era5.sel(site=sitecode)
        except:
            if len(era5.site) > 1:
                print("No ERA5-Land data available for "+str(sitecode))
                return
            else:
                era5site = era5  # If user only has one site it breaks here - this stops that

        df = pd.DataFrame()
        df['DT'] = pd.to_datetime(era5site.time.values)
        df['TEMP'] = era5site.temperature.values-273.15
        df['PRCP'] = era5site.precipitation.values*1000
        df['YEAR'] = df['DT'].dt.year
        df['MONTH'] = df['DT'].dt.month
        df['HOUR'] = df['DT'].dt.hour
        # Remove values not at midnight to account for era5 accumulation
        df.loc[df['HOUR'] != 0, 'PRCP'] = 0

    uniqueyears = df['YEAR'].unique()
    uniqueyears = uniqueyears[~np.isnan(uniqueyears)]  # remove nans
    dfdicts = dict()

    for i in range(len(uniqueyears)):
        dfyr = df.loc[df['YEAR'] == uniqueyears[i]]
        tmp = dfyr.groupby(['MONTH']).mean()
        tmpprcp = dfyr.groupby(['MONTH']).sum()
        tmp['PRCP'] = tmpprcp['PRCP']
        dfdicts[i] = tmp

    KG_all = []
    MAPs = []
    MATs = []
    for i in range(len(dfdicts)):
        df = dfdicts[i]

        one = []
        two = []
        three = []

        # CALCULATE THE VALUES FOR THE CONDITIONALS
        Tcold = df['TEMP'].min()
        Thot = df['TEMP'].max()
        Pdry = df['PRCP'].min()
        MAP = df['PRCP'].sum()
        MAT = df['TEMP'].mean()
        # Check if errors in data
        if (math.isnan(Thot)) or (math.isnan(Pdry)) or (math.isnan(Tcold)) or (math.isnan(MAP)) or (math.isnan(MAT)):
            print("Found NaN values so cannot computer KG, skipping year " +
                  str(uniqueyears[i])+"!")
            continue
        else:
            pass

        try:
            season1 = df.loc[[1, 2, 3, 10, 11, 12]]
            season2 = df.loc[[4, 5, 6, 7, 8, 9]]
            if season1['TEMP'].mean() > season2['TEMP'].mean():
                summer = season1.copy()
                winter = season2.copy()
            else:
                summer = season2.copy()
                winter = season1.copy()
            Psdry = summer['PRCP'].min()
            Pwdry = winter['PRCP'].min()
            Pswet = summer['PRCP'].max()
            Pwwet = winter['PRCP'].min()
            # Check for Pthresh
            if (winter['PRCP'].sum()/MAP)*100 >= 70:
                Pthresh = 2*MAT
            elif (summer['PRCP'].sum()/MAP)*100 >= 70:
                Pthresh = 2*MAT+28
            else:
                Pthresh = 2*MAT+14
            Tmon10 = sum(df['TEMP'] > 10)

            # Big nested conditionals for KG
            if Tcold >= 18:
                one = "A"
                if Pdry >= 60:
                    two = "f"
                elif Pdry >= 100-(MAP/25):
                    two = "m"
                else:
                    two = "w"
            elif MAP < 10*Pthresh:
                one = "B"
                if MAP < 5*Pthresh:
                    two = "W"
                    if MAT >= 18:
                        three = "h"
                    else:
                        three = "k"
                else:
                    two = "S"
                    if MAT >= 18:
                        three = "h"
                    else:
                        three = "k"
            elif Thot > 10 and 0 < Tcold < 18:
                one = "C"
                if Psdry < 40 and Psdry < (Pwwet/3):
                    two = "s"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    else:
                        three = "c"
                elif Pwdry < (Pswet/10):
                    two = "w"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    else:
                        three = "c"
                else:
                    two = "f"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    else:
                        three = "c"
            elif Thot > 10 and Tcold <= 0:
                one = "D"
                if Psdry < 40 and Psdry < (Pwwet/3):
                    two = "s"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    elif Tcold < -38:
                        three = "d"
                    else:
                        three = "c"
                elif Pwdry < (Pswet/10):
                    two = "w"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    elif Tcold < -38:
                        three = "d"
                    else:
                        three = "c"
                else:
                    two = "f"
                    if Thot >= 22:
                        three = "a"
                    elif Tmon10 >= 4:
                        three = "b"
                    elif Tcold < -38:
                        three = "d"
                    else:
                        three = "c"
            elif Thot < 10:
                one = "E"
                if Thot > 0:
                    two = "T"
                else:
                    two = "F"

            KG = one+two+three
            KG_all.append(KG)
            MAPs.append(MAP)
            MATs.append(MAT)
        except:
            print("Full year of data unavailable for " +
                  str(uniqueyears[i])+" skipping year")

    KG_all = pd.DataFrame(KG_all)
    MAPs = np.asarray(MAPs)
    MATs = np.asarray(MATs)

    MAPavg = MAPs.mean()
    MATavg = MATs.mean()
    KG_final = KG_all.mode()
    KG_final = KG_final[0]
    KG_final = KG_final[0]
    return KG_final, MAPavg, MATavg
###################### Fill in metadata ######################################


def fill_metadata(meta, calc_beta=True, land_cover=True, agb=True, nld=nld):
    """fill_metadata reads in meta_data table, uses the latitude and longitude of each site to find
    metadata from the ISRIC soil database, as well as calculating reference pressure
    and beta coefficient.

    Parameters
    ----------
    meta : dataframe
        metadata dataframe
    calc_beta : bool, optional
        whether to calculate the beta coefficient for the sites, by default True
    land_cover : bool, optional
        whether to extract the lang cover data for the sites, by default True
    agb : bool, optional
        whether to extract the above ground biomass data for the sites, by default True
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    dataframe
        returns the metadata dataframes with the values added
    """
    nld=nld['config']

    meta['SITENUM'] = meta.SITENUM.map("{:03}".format)  # Ensure leading zeros

    for i in range(len(meta['LATITUDE'])):
        print(i)

        try:
            lat = meta['LATITUDE'][i]
            lon = meta['LONGITUDE'][i]
            country = meta['COUNTRY'][i]
            sitenum = meta['SITENUM'][i]

            resdict = isric_variables(lat, lon)
            wrb = isric_wrb_class(lat, lon)

            # Bulk Density
            bdod = isric_depth_mean(resdict, 0)
            bdod = bdod/100  # convert to decimal fraction
            bdoduc = isric_depth_uc(resdict, 0)
            bdoduc = bdoduc/100

            # Cation Exchange Capacity
            cec = isric_depth_mean(resdict, 1)
            cecuc = isric_depth_uc(resdict, 1)

            # Coarse Fragment Volume
            cfvo = isric_depth_mean(resdict, 2)
            cfvo = cfvo/10  # convert to decimal fraction
            cfvouc = isric_depth_uc(resdict, 2)
            cfvouc = cfvouc/10

            # Clay as prcnt
            clay = isric_depth_mean(resdict, 3)
            clay = clay/1000  # convert to decimal fraction
            clayuc = isric_depth_uc(resdict, 3)
            clayuc = clayuc/1000

            # Nitrogen
            nitro = isric_depth_mean(resdict, 4)
            nitro = nitro/100  # convert to g/kg
            nitrouc = isric_depth_uc(resdict, 4)
            nitrouc = nitrouc/100

            # OCD CURRENTLY DATA APPEARS TO ALWAYS BE NONETYPE - REMOVED
           # ocd = isric_depth_mean(resdict, 5)
           # ocd = ocd/1000 # convert to kg/dm**3
           # ocduc = isric_depth_uc(resdict, 5)
           # ocduc = ocduc/1000

            # phh20
            phh20 = isric_depth_mean(resdict, 6)
            phh20 = phh20/10  # convert to pH
            phh20uc = isric_depth_uc(resdict, 6)
            phh20uc = phh20uc/10

            # Sand
            sand = isric_depth_mean(resdict, 7)
            sand = sand/1000  # convert to decimal fraction
            sanduc = isric_depth_uc(resdict, 7)
            sanduc = sanduc/1000

            # Silt
            silt = isric_depth_mean(resdict, 8)
            silt = silt/1000  # convert to decimal fraction
            siltuc = isric_depth_uc(resdict, 8)
            siltuc = siltuc/1000

            # SOC
            soc = isric_depth_mean(resdict, 9)
            soc = soc/1000  # convert to decimal fraction
            socuc = isric_depth_uc(resdict, 9)
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
            meta.at[i, 'SOIL_TEXTURE'] = soil_texture(sand, silt, clay)

            # ADD LAND COVER
            if land_cover == True:
                try:
                    lc = find_lc(lat, lon)
                    meta.at[i, 'LAND_COVER'] = lc
                except:
                    print("No land cover data found... skipping")
                    pass
            else:
                pass

            # ADD ABOVE GROUND BIOMASS
            if agb == True:
                try:
                    agb = get_agb(lat, lon)
                    meta.at[i, 'AGBWEIGHT'] = agb
                except:
                    print("No AGB data found... skipping")
                    pass
            else:
                pass

            if meta['BD'][i] != None:
                try:
                    bd = meta.at[i, 'BD']
                    meta.at[i, 'SM_MAX'] = (1-(bd/(nld['density'])))
                except:
                    print(
                        "Could not convert bulk density to soil moisture max. Check your units please.")
            else:
                bd = meta.at[i, 'BD_ISRIC']
                meta.at[i, 'SM_MAX'] = (1-(bd/(int(nld['density']))))

            # ADD KG climate
            kg, meanprecip, meantemp = KG_func(meta, country, sitenum)
            meta.at[i, 'KG_CLIMATE'] = kg
            meta.at[i, 'MEAN_ANNUAL_PRECIP'] = meanprecip
            meta.at[i, 'MEAN_ANNUAL_TEMP'] = meantemp
        except:
            pass

    if calc_beta == True:
        print("Calculating Beta Coeff...")

        meta['BETA_COEFF'], meta['REFERENCE_PRESS'] = betacoeff(meta['LATITUDE'],
                                                                meta['ELEV'], meta['GV'])
    else:
        pass

    meta.to_csv(nld['defaultdir'] + "/data/metadata.csv",
                header=True, index=False, mode='w')

    return meta
