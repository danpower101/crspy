"""
Process The Data

author: Daniel Power - University of Bristol PhD candidate
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

def prepare_data(fileloc):
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
    lon = meta.loc[(meta.SITENUM == sitenum) & (meta.COUNTRY == country), "LONGITUDE"].item()
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
    #                         Collect meta_data                                   #
    ###############################################################################     
    print("Collecting additional meta data for site...")
    #Collect variables from ISRIC API for the relevant 250m grid
    resdict = smoon.isric_variables(lat, lon)
    wrb = smoon.isric_wrb_class(lat, lon)
    
    """
    Each variable will be coded like below with mapped units as below:
    0=bdod  - bulk density - (cg/cm**3)
    1=cec - cation exchange capacity - (mmol(c))
    2=cfvo - coarse fragment volume - (cm**3/dm**3)
    3=clay (g/kg)
    4=nitrogen (cg/kg)
    5=ocd - organic carbon density - (kg/dm**3)
    6=phh20 -pH of Water - (pHx10)
    7=sand (g/kg)
    8=silt  (g/kg)
    9=soc - soil organic carbon (dg/kg)
    """
    #Bulk Density
    bdod = smoon.isric_depth_mean(resdict, 0)
    bdod = bdod/100 # convert to decimal fraction
    bdoduc = smoon.isric_depth_uc(resdict, 0)
    bdoduc = bdoduc/100
    
    #Cation Exchange Capacity
    cec = smoon.isric_depth_mean(resdict, 1)
    cecuc = smoon.isric_depth_uc(resdict, 1)

    # Coarse Fragment Volume
    cfvo = smoon.isric_depth_mean(resdict, 2)
    cfvo = cfvo/10 # convert to decimal fraction
    cfvouc = smoon.isric_depth_uc(resdict, 2)
    cfvouc = cfvouc/10

    # Clay as prcnt
    clay = smoon.isric_depth_mean(resdict, 3)
    clay = clay/1000 # convert to decimal fraction
    clayuc = smoon.isric_depth_uc(resdict, 3)
    clayuc = clayuc/1000

    # Nitrogen
    nitro = smoon.isric_depth_mean(resdict, 4)
    nitro = nitro/100 # convert to g/kg
    nitrouc = smoon.isric_depth_uc(resdict, 4)
    nitrouc = nitrouc/100

    #OCD CURRENTLY DATA APPEARS TO ALWAYS BE NONETYPE - REMOVED
   # ocd = smoon.isric_depth_mean(resdict, 5)
   # ocd = ocd/1000 # convert to kg/dm**3
   # ocduc = smoon.isric_depth_uc(resdict, 5)
   # ocduc = ocduc/1000

    #phh20
    phh20 = smoon.isric_depth_mean(resdict, 6)
    phh20 = phh20/10 # convert to pH
    phh20uc = smoon.isric_depth_uc(resdict, 6)
    phh20uc = phh20uc/10

    #Sand
    sand = smoon.isric_depth_mean(resdict, 7)
    sand = sand/1000 # convert to decimal fraction
    sanduc = smoon.isric_depth_uc(resdict, 7)
    sanduc = sanduc/1000

    #Silt
    silt = smoon.isric_depth_mean(resdict, 8)
    silt = silt/1000 # convert to decimal fraction
    siltuc = smoon.isric_depth_uc(resdict, 8)
    siltuc = siltuc/1000    
    
    #SOC
    soc  = smoon.isric_depth_mean(resdict, 9)
    soc = soc/1000 # convert to decimal fraction
    socuc = smoon.isric_depth_uc(resdict, 9)
    socuc = socuc/1000   
    
    
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'BD_ISRIC'] = bdod
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'BD_ISRIC_UC'] = bdoduc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SOC_ISRIC'] = soc
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SOC_ISRIC_UC'] = socuc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'pH_H20_ISRIC'] = phh20
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'pH_H20_ISRIC_UC'] = phh20uc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CEC_ISRIC'] = cec
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CEC_ISRIC_UC'] = cecuc    
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CFVO_ISRIC'] = cfvo
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CFVO_ISRIC_UC'] = cfvouc    
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'NITROGEN_ISRIC'] = nitro
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'NITROGEN_ISRIC_UC'] = nitrouc

    #meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'OCD_ISRIC'] = ocd
    #meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'OCD_ISRIC_UC'] = ocduc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SAND_ISRIC'] = sand
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SAND_ISRIC_UC'] = sanduc

    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SILT_ISRIC'] = silt
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'SILT_ISRIC_UC'] = siltuc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CLAY_ISRIC'] = clay
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'CLAY_ISRIC_UC'] = clayuc
    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'TEXTURE'] = smoon.soil_texture(sand, silt, clay)    
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'WRB_ISRIC'] = wrb
    
    print("Done")
    
    ################### Collect land data ########################
    
    lc = smoon.find_lc(lat, lon)
    meta.loc[(meta['SITENUM'] == sitenum) & (meta['COUNTRY'] == country), 'LAND_COVER'] = lc
    
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

    meta.to_csv(nld['defaultdir'] + "/data/meta_data.csv", header=True, index=False, mode='w')
	# Save Tidy data
    df.to_csv(nld['defaultdir'] + "/data/crns_data/tidy/"+country+"_SITE_" + sitenum+"_TIDY.txt", 
          header=True, index=False, sep="\t",  mode='w')
    print("Done")
    return df, country, sitenum, meta