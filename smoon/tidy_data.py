"""
Process The Data

author: Daniel Power - University of Bristol PhD student
email: daniel.power@bristol.ac.uk

This code will analyse the raw neutron counts  of a site. It will do this in a 
few steps. First it will input level 1 and 2 data and combine the tables with 
the required info. Second it will begin to analyse this info and correct neutron 
counts based on Pressure, Water Humidity, Solar Intensity and Above Ground Biomass.    

"""
from name_list import nld
import os
os.chdir(nld['defaultdir'])
import pandas as pd # Pandas for dataframe
import re
import smoon
import datetime
import xarray as xr
import pylab
import sys
pylab.show()

###############################################################################
#                       Get list of files                                     #
###############################################################################

def dropemptycols(colstocheck, df1):
    
    """
    Drop any columns that are empty (i.e. all -999).
    """
    for i in range(len(colstocheck)):
        col = colstocheck[i]
        if df1[col].mean() == -999:
            df1 = df1.drop([col], axis=1)
        else:
            pass
    return df1

def tidyup(fileloc):
    """
    Read in meta_data. Format DateTime. Check for external vars. If not availble
    use ERA5-Land data (additional module to obtain this)
    """
    print("~~~~~~~~~~~~~ Start TidyUp ~~~~~~~~~~~~~")
    ###############################################################################
    #                        Import Data and                                      #
    #                       organise time and date                                #
    ###############################################################################
    
    meta = pd.read_csv(nld['defaultdir'] + "/data/meta_data.csv")
    meta['SITENUM'] = meta.SITENUM.map("{:03}".format) # Add leading zeros
    
    # Extract the country and site number from file name
    
    tmp = fileloc
    m = re.search('/crns_data/raw/(.+?)_', tmp) #  (.+?) here is the string being extracted between the series
    if m:
        country = m.group(1)
    m2 = re.search('SITE_(.+?).txt', tmp)
    if m2:
        sitenum = m2.group(1)
    
    sitecode = country+"_SITE_"+sitenum #create full title for use on ERA5Land data
    
    # Read in files and sort time and date columns
    df = pd.read_csv(nld['defaultdir'] + "/data/crns_data/raw/"+country+"_SITE_" + sitenum+".txt", sep="\t")
    tmp = df['TIME'].str.split(" ", n=1, expand=True)
    df['DATE'] = tmp[0]
    df['TIME'] = tmp[1]
    new = df["TIME"].str.split(":", n = 2, expand = True) 
    df['DT'] = pd.to_datetime(df['DATE']) 
    my_time = df['DT']
    time = pd.DataFrame()
    
    tseries=[]
    for i in range(len(new)): # Loop through with loc to append the hours onto a DateTime object
        time= my_time[i] + datetime.timedelta(hours=int(new.loc[i,0]),minutes=int(new.loc[i,1])) # time = the datetime plus the hours and mins in time delta
        tseries.append(time) # Append onto tseries
        
    df['DT'] = tseries      # replace DT with tseries which now has time as well
    
    ###############################################################################
    #                        Beta Coefficient                                     #
    ###############################################################################
    print("Calculate Beta Coeff...")
    
    avgp = meta.loc[(meta.SITENUM == sitenum) & (meta.COUNTRY == country), "MEAN_PRESS"].item()
    elev = meta.loc[(meta.SITENUM == sitenum) & (meta.COUNTRY == country), "ELEV"].item()
    lat = meta.loc[(meta.SITENUM == sitenum) & (meta.COUNTRY == country), "LATITUDE"].item()
    r_c = meta.loc[(meta.SITENUM == sitenum) & (meta.COUNTRY == country), "GV"].item()
    beta, refpress = smoon.betacoeff(avgp, lat, elev, r_c)
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'BETA_COEFF'] = abs(beta)
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'REFERENCE_PRESS'] = refpress
    meta.to_csv(nld['defaultdir']+"/data/meta_data.csv", header=True, index=False, mode="w") #write to csv
    print("Done")
    ###############################################################################
    #                        The Master Time                                      #
    ###############################################################################
    """
    Master Time creates a time series from first data point to last data point with
    every hour created. This is to remedy the gaps in the data and allow mapping 
    between CRNS data and ERA5_Land variables.
    
    DateTime is standardised to be on the hour (using floor). This can create issues
    with "duplicated" data points, usually when errors in logging have created data
    every half hour instead of every hour, for example. The best way to address this 
    currently is to retain the first instance of the duplicate and discard the second.
    """
    print("Master Time process...")
    df['DT'] = df.DT.dt.floor(freq = 'H')
    df = df.set_index(df.DT)
    df['dupes'] = df.duplicated(subset="DT")
    # Add a save for dupes here - need to test a selection of sites to see 
    # whether dupes are the same. 
    df.to_csv(nld['defaultdir'] + "/data/crns_data/dupe_check/"+country+"_SITE_" + sitenum+"_DUPES.txt",
          header=True, index=False, sep="\t",  mode='w')
    df = df.drop(df[df.dupes == True].index)
    idx = pd.date_range(df.DATE.iloc[0], df.DATE.iloc[-1], freq='1H', closed='left')
    df = df.reindex(idx, fill_value=nld['noval'])
    df['DT'] = df.index
    print("Done")
    ###############################################################################
    #                         ERA-5 variables                                     #
    ###############################################################################    
    """
    Read in netcdfs in a loop - attaching data for each variable to df. 
    """
    print("Collecting ERA-5 Land variables...")
    era5 = xr.open_dataset(nld['defaultdir']+"data/era5land/"+nld['era5_filename']+".nc") #
    era5site = era5.sel(site=sitecode)
    era5time = pd.to_datetime(era5site.time.values)
    
    temp_dict = dict(zip(era5time, era5site.temperature.values-273.15)) # minus 273.15 to convert to celcius as era5 stores it as kelvin
    prcp_dict = dict(zip(era5time, era5site.precipitation.values))
    dptemp_dict = dict(zip(era5time, era5site.dewpoint_temperature.values-273.15))    
    press_dict = dict(zip(era5time, era5site.pressure.values*0.01)) # Want to check on this
    swe_dict = dict(zip(era5time,era5site.snow_water_equiv.values))
    
    # Add the ERA5_Land data 
    if df.E_TEM.mean() == -999:
        df['TEMP'] = df['DT'].map(temp_dict)
        meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'TEM_DATA_SOURCE'] = 'ERA5_Land'
    else:
        pass
    
    if df.RAIN.mean() == -999:
        df['RAIN'] = df['DT'].map(prcp_dict)
        meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'RAIN_DATA_SOURCE'] = 'ERA5_Land'
    else:
        print ('You now need to fix RAIN issue. Line 136')
        sys.exit()
    
    df['DEWPOINT_TEMP'] = df['DT'].map(dptemp_dict)   
    df['SWE'] = df['DT'].map(swe_dict)
    df['ERA5L_PRESS'] = df['DT'].map(press_dict)

    # PRESS2 is more accurate pressure gauge - use if available
    df['PRESS'] = df['PRESS2']
    df.loc[df['PRESS'] == -999, 'PRESS'] = df['PRESS1']

    df['VP'] = df.apply(lambda row: smoon.dew2vap(row['DEWPOINT_TEMP']), axis=1) # VP is in kPA
    df['VP'] = df['VP']*1000 # Convert to Pascals
    print("Done")
    ###############################################################################
    #                            The Final Table                                  #
    #                                                                             #
    # Add function that checks to see if column is all -999 - if so drop column   #
    ###############################################################################
    print("Writing out table...")
    # REMINDER - remove 2019 dates as no DAYMET data
    
    df = df.reindex( columns = ['DT','MOD','UNMOD','PRESS','I_TEM','I_RH','E_TEM',
                                      'E_RH','BATT','TEMP','RAIN', 'DEWPOINT_TEMP','VP','SWE','fsol',
                                      'JUNG_COUNT','fbar','VWC1','VWC2','VWC3', 'ERA5L_PRESS'])
    
    df = df[['DT','MOD','UNMOD','PRESS','I_TEM','I_RH','E_TEM','E_RH','BATT','TEMP',
         'RAIN','VP','DEWPOINT_TEMP','SWE',
         'JUNG_COUNT','VWC1','VWC2','VWC3','fbar', 'fsol']]
    
    # Add list of columns that some sites wont have data on - removes them if empty
    df = dropemptycols(['VWC1', 'VWC2', 'VWC3', 'E_TEM', 'E_RH'], df)
    df = df.round(3)
    #Change Order 

    
	# Save Tidy data
    df.to_csv(nld['defaultdir'] + "/data/crns_data/tidy/"+country+"_SITE_" + sitenum+"_TIDY.txt", 
          header=True, index=False, sep="\t",  mode='w')
    print("Done")
    return df, country, sitenum, meta