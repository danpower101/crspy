"""
Process The Data

author: Daniel Power - University of Bristol PhD candidate
email: daniel.power@bristol.ac.uk

This code will analyse the raw neutron counts  of a site. It will do this in a 
few steps. First it will input level 1 and 2 data and combine the tables with 
the required info. Second it will begin to analyse this info and correct neutron 
counts based on Pressure, Water Humidity, Solar Intensity and Above Ground Biomass.    

"""

import pylab
import xarray as xr
import datetime
import re
import numpy as np
import pandas as pd  # Pandas for dataframe
pylab.show()

from crspy.neutron_correction_funcs import (es, ea, dew2vap)
from crspy.additional_metadata import nmdb_get
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')

###############################################################################
#                       Get list of files                                     #
###############################################################################


def dropemptycols(colstocheck, df, nld=nld):
    """dropemptycols drop any columns that are empty (i.e. all -999)

    Parameters
    ----------
    colstocheck : str
        string of column title to check
    df : dataframe  
        dataframe to check

    """
    nld=nld['config']
    for i in range(len(colstocheck)):
        col = colstocheck[i]
        if col in df:
            try:
                if df[col].mean() == int(nld['noval']):
                    df = df.drop([col], axis=1)
                else:
                    pass
            except:
                pass
        else:
            pass
    return df


def prepare_data(fileloc, intentype=None, nld=nld):
    """prepare_data provided with the location of the raw data it will prepare the data.

    Steps include: 
        - Find the country and sitenum from text file title
        - Fix time to be on the hour rather than variable
        - Check what data is available - if any is missing fill with ERA5_Land data
        - Collect Jungfraujoch neutron monitor data from NMDB.eu for the timescale here
        - Final tidy of columns

    Parameters
    ----------
    fileloc : str   
        string of the location of the file on the users computer
    intentype : str, optional
        can be set to nearestGV if using the alternative method, by default None
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']

    print("~~~~~~~~~~~~~ Start TidyUp ~~~~~~~~~~~~~")
    ###############################################################################
    #                        Import Data and                                      #
    #                       organise time and date                                #
    ###############################################################################

    meta = pd.read_csv(nld['defaultdir'] + "/data/metadata.csv")
    meta['SITENUM'] = meta.SITENUM.map("{:03}".format)  # Add leading zeros

    # Extract the country and site number from file name

    tmp = fileloc
    # (.+?) here is the string being extracted between the series
    m = re.search('/crns_data/raw/(.+?)_', tmp)
    if m:
        country = m.group(1)
    else:
        print("Could not find country from file name...")
        
    m2 = re.search('SITE_(.+?).txt', tmp)
    if m2:
        sitenum = m2.group(1)
    else:
        print("Could not find country from file name...")
        

    sitecode = country+"_SITE_"+sitenum  # create full title for use on ERA5Land data

    # Read in files and sort time and date columns
    df = pd.read_csv(nld['defaultdir'] + "/data/crns_data/raw/" +
                     country+"_SITE_" + sitenum+".txt", sep="\t")

    # Remove leading white space - present in some SD card data
    df['TIME'] = df['TIME'].str.lstrip()
    # Ensure using dashes as Excel tends to convert to /s
    if '/' in df['TIME'][0]:
        df['TIME'] = df['TIME'].str.replace('/', '-')
    else:
        pass
    tmp = df['TIME'].str.split(" ", n=1, expand=True)
    df['DATE'] = tmp[0]
    df['TIME'] = tmp[1]
    new = df["TIME"].str.split(":", n=2, expand=True)
    df['DT'] = pd.to_datetime(df['DATE'])
    my_time = df['DT']
    time = pd.DataFrame()

    tseries = []
    for i in range(len(new)):  # Loop through with loc to append the hours onto a DateTime object
        # time = the datetime plus the hours and mins in time delta
        time = my_time[i] + datetime.timedelta(
            hours=int(new.loc[i, 0]), minutes=int(new.loc[i, 1]))
        tseries.append(time)  # Append onto tseries

    df['DT'] = tseries      # replace DT with tseries which now has time as well

    # Collect dates here to prevent issues with nan values after mastertime - for use in Jungrafujoch process
    startdate = str(df['DATE'].iloc[0])
    enddate = str(df['DATE'].iloc[-1])

    ###############################################################################
    #                        The Master Time                                      #
    ###############################################################################
    """
    Master Time creates a time series from first data point to last data point with
    every hour created. This is to remedy the gaps in the data and allow mapping 
    between CRNS data and ERA5_Land variables.
    
    DateTime is standardised to be on the hour (using floor). This can create issues
    with "duplicated" data points, usually when errors in logging have created data
    every half hour instead of every hour, for example. 
    
    The best way to address this currently is to retain the first instance of the 
    duplicate and discard the second.
    """
    print("Master Time process...")
    df['DT'] = df.DT.dt.floor(freq='H')
    dtcol = df['DT']
    df.drop(labels=['DT'], axis=1, inplace=True)  # Move DT to first col
    df.insert(0, 'DT', dtcol)

    
    df['dupes'] = df.duplicated(subset="DT")
    # Add a save for dupes here - need to test a selection of sites to see
    # whether dupes are the same.
    df.to_csv(nld['defaultdir'] + "/data/crns_data/dupe_check/"+country+"_SITE_" + sitenum+"_DUPES.txt",
              header=True, index=False, sep="\t",  mode='w')
    df = df.drop(df[df.dupes == True].index)
    df = df.set_index(df.DT)
    if df.DATE.iloc[0] > df.DATE.iloc[-1]:
        raise Exception(
            "The dates are the wrong way around, see crspy.flipall() to fix it")

    idx = pd.date_range(
        df.DATE.iloc[0], df.DATE.iloc[-1], freq='1H', closed='left')
    df = df.reindex(idx, fill_value=np.nan)
    df = df.replace(np.nan, int(nld['noval'])) # add replace to make checks on whole cols later

    df['DT'] = df.index
    print("Done")
    ###############################################################################
    #                         ERA-5 variables                                     #
    ###############################################################################
    """
    Read in netcdfs in a loop - attaching data for each variable to df. 
    
    For temperature and rain it will check to see if they are missing (i.e. all values
    are -999). If this is true it will use ERA5_Land data to fill in - if it is false it will use
    local data.
    """

    #!!! TO DO add a check here to see if we need ERA5_Land data in the first place

    # Read in the time zone of the site
    print("Collecting ERA-5 Land variables...")
    try:
        era5 = xr.open_dataset(
            nld['defaultdir']+"/data/era5land/"+nld['era5_filename']+".nc")
        print('Read in file')
        try:
            era5site = era5.sel(site=sitecode)
        except:
            era5site = era5  # If user only has one site it breaks here - this stops that

        era5time = pd.to_datetime(era5site.time.values)

        # minus 273.15 to convert to celcius as era5 stores it as kelvin
        temp_dict = dict(zip(era5time, era5site.temperature.values-273.15))
        dptemp_dict = dict(
            zip(era5time, era5site.dewpoint_temperature.values-273.15))
        # Want to check on this
        press_dict = dict(zip(era5time, era5site.pressure.values*0.01))
        swe_dict = dict(zip(era5time, era5site.snow_water_equiv.values*1000))
        # prcp is in meteres in ERA5 so convert to mm
        prcp_dict = dict(zip(era5time, era5site.precipitation.values*1000))
        # Introduced here to "correct" for the way ERA5_Land accumulates precipitation over 24 hours
        tmp = pd.DataFrame()
        tmp['DT'] = era5time
        tmp['RAIN'] = tmp['DT'].map(prcp_dict)
        tmp['DT'] = pd.to_datetime(tmp['DT'])
        tmp['YEAR'] = tmp['DT'].dt.date
        tmp['HOUR'] = tmp['DT'].dt.hour
        tmp['RAINSHIFT'] = tmp['RAIN'].shift(1)
        tmp['HOURLYRAIN'] = 0
        tmp['TRUERAIN'] = tmp['RAIN'] - tmp['RAINSHIFT']
        tmp.loc[tmp['HOUR'] == 1, ['TRUERAIN']] = tmp['RAIN']

        prcp_dict = dict(zip(tmp['DT'], tmp['TRUERAIN']))
        # Add the ERA5_Land data
        if df.E_TEM.mean() == int(nld['noval']):
            df['TEMP'] = df['DT'].map(temp_dict)
            meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY']
                                                     == country), 'TEM_DATA_SOURCE'] = 'ERA5_Land'
        else:
            df['TEMP'] = df['E_TEM']
            meta.loc[(meta['SITENUM'] == sitenum) & (
                meta['COUNTRY'] == country), 'TEM_DATA_SOURCE'] = 'Local'

        if df.RAIN.mean() == int(nld['noval']):
            df['RAIN'] = df['DT'].map(prcp_dict)
            meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY']
                                                     == country), 'RAIN_DATA_SOURCE'] = 'ERA5_Land'
        else:
            meta.loc[(meta['SITENUM'] == sitenum) & (
                meta['COUNTRY'] == country), 'RAIN_DATA_SOURCE'] = 'Local'

        if df.E_RH.mean() == int(nld['noval']):
            rh = False
            meta.loc[(meta['SITENUM'] == sitenum) & (
                meta['COUNTRY'] == country), 'RH_DATA_SOURCE'] = 'None'
        else:
            meta.loc[(meta['SITENUM'] == sitenum) & (
                meta['COUNTRY'] == country), 'RH_DATA_SOURCE'] = 'Local'
            rh = True
        df['DEWPOINT_TEMP'] = df['DT'].map(dptemp_dict)
        df['SWE'] = df['DT'].map(swe_dict)
        df['ERA5L_PRESS'] = df['DT'].map(press_dict)

        # PRESS2 is more accurate pressure gauge - use if available and if not fill in with PRESS1
        press_series = df['PRESS2']
        df['PRESS'] = df['PRESS2']
        
        df.loc[df['PRESS'] == int(nld['noval']), 'PRESS'] = df['PRESS1']
        df = df.replace(int(nld['noval']), np.nan)

        if rh == False:
            df['VP'] = df.apply(lambda row: dew2vap(
                row['DEWPOINT_TEMP']), axis=1)  # VP is in kPA
            df['VP'] = df['VP']*1000  # Convert to Pascals
        else:
            # Output is in hectopascals
            df['es'] = df.apply(lambda row: es(row['TEMP']), axis=1)
            df['es'] = df['es']*100  # Convert to Pascals
            df['VP'] = df.apply(lambda row: ea(row['es'], row['E_RH']), axis=1)

        print("Done")
    except:
        # Introduced this bit to allow using sites that don't need ERA5_Land
        df['PRESS'] = df['PRESS2']
        df.loc[df['PRESS'] == int(nld['noval']), 'PRESS'] = df['PRESS1']  # !!!added
        df = df.replace(int(nld['noval']), np.nan)

        df['TEMP'] = df['E_TEM']

        df['es'] = df.apply(lambda row: es(row['TEMP']),
                            axis=1)  # Output is in hectopascals
        df['es'] = df['es']*100  # Convert to Pascals
        df['VP'] = df.apply(lambda row: ea(row['es'], row['E_RH']), axis=1)
        print("Cannot load era5_land data. Please download data as it is needed.")

    ###############################################################################
    #                         Jungfraujoch data                                   #
    ###############################################################################
    if intentype == "nearestGV":

        nmdblist = pd.read_csv(nld['defaultdir']+"/data/nmdb_stations.csv")
        nmdblist = dict(zip(nmdblist['Station_Code'], nmdblist['GV']))
        sitegv = meta.loc[(meta.SITENUM == sitenum) & (
            meta.COUNTRY == country), "GV"].item()
        key, value = min(nmdblist.items(), key=lambda x: abs(sitegv - x[1]))
        print("Getting NMDB data from "+str(key))
        nmdbdict = nmdb_get(startdate, enddate, station=str(key))
        df['NMDB_COUNT'] = int(nld['noval'])  # make sure its empty
        df['NMDB_COUNT'] = df['DT'].map(nmdbdict)
        # Keep as Jung Count to save changing scripts
        df['NMDB_COUNT'] = df['NMDB_COUNT'].astype(float)
        nmdbstation = str(key)
    else:
        print("Getting Jungfraujoch counts...")

        try:
            nmdbdict = nmdb_get(startdate, enddate)
            df['NMDB_COUNT'] = int(nld['noval']) # make sure its empty
            df['NMDB_COUNT'] = df['DT'].map(nmdbdict)
            df['NMDB_COUNT'] = df['NMDB_COUNT'].astype(float)
            print("Done")
        except:
            print("NMDB down")
        ###############################################################################
    #                            The Final Table                                  #
    #                                                                             #
    # Add function that checks to see if column is all -999 - if so drop column   #
    ###############################################################################
    print("Writing out table...")
    # REMINDER - remove 2019 dates as no DAYMET data

    def movecol(col, location):
        """
        Move columns to a specific position.
        """
        tmp = df[col]
        df.drop(labels=[col], axis=1, inplace=True)  # Move DT to first col
        df.insert(location, col, tmp)

    # Move below columns as like them at the front
    movecol("MOD", 1)
    try:
        movecol("UNMOD", 2)
    except:
        df.insert(2, "UNMOD", np.nan)  # filler for if UNMOD is unavailble
    movecol("PRESS", 3)
    movecol("TEMP", 4)

    df.drop(labels=['TIME', 'PRESS1', 'PRESS2', 'DATE', 'dupes'],
            axis=1, inplace=True)  # not required after here
    try:
        df.drop(labels=['fsol'], axis=1, inplace=True)
    except:
        pass
    # Add list of columns that some sites wont have data on - removes them if empty
    df = dropemptycols(df.columns.tolist(), df)
    df = df.round(3)
    df = df.replace(np.nan, int(nld['noval']))
    # SD card data had some 0 values - should be nan
    df['MOD'] = df['MOD'].replace(0, int(nld['noval']))
    # Change Order

    meta.to_csv(nld['defaultdir'] + "/data/metadata.csv",
                header=True, index=False, mode='w')
    # Save Tidy data
    df.to_csv(nld['defaultdir'] + "/data/crns_data/tidy/"+country+"_SITE_" + sitenum+"_TIDY.txt",
              header=True, index=False, sep="\t",  mode='w')
    print("Done")
    if intentype != None:
        return df, country, sitenum, meta, nmdbstation
    else:
        return df, country, sitenum, meta
