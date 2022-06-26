"""
Created on Wed Aug 28 15:20:35 2019

@author: Daniel Power
Email: daniel.power@bristol.ac.uk


"""
import pandas as pd
import numpy as np
import math

# crspy funcs
from crspy.n0_calibration import (rscaled, D86)
from crspy.graphical_functions import colourts
from crspy.gen_funcs import theta_calc, theta_kohli, checkdata
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')


###############################################################################
#                       Add the sitenum/country                               #
###############################################################################
"""

"""
## NOTE: theta_calc has been moved to gen_funcs.py


def thetaprocess(df, meta, country, sitenum, agg24, yearlysmfig=True, theta_method="desilets", nld=nld):
    """thetaprocess takes the dataframe provided by previous steps and uses the theta calculations
    to give an estimate of soil moisture. 

    Constants are taken from meta data which is identified using the "country" and "sitenum"
    inputs. 

    Realistic values are provided by constraining soil moisture estimates to physically possible values.
        i.e. Nothing below 0 and max values based on porosity at site.

    Provides an estimated depth of measurement using the D86 function from Shcron et al., (2017)

    Gives running averages of measurements using a 12 hour window. To handle missing 
    data a minimum of 6 hours of data per 12 hour window is required, otherwise one
    missing hour could lead to large gaps in 12 hour means. 

    Parameters
    ----------
    df : dataframe 
        dataframe of CRNS data
    meta : dataframe
        dataframe of metadata
    country : str
        country e.g. "USA"
    sitenum : str  
        sitenum e.g. "011"
    agg24 : bool
        input from full process wrapper on whether to calc agg24 vals 
        TODO: consider whether this needs to be done earlier in process
    yearlysmfig : bool, optional
        whether to output yearly figures when creating time series, by default True
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars
    """
    nld=nld['config']
    print("~~~~~~~~~~~~~ Estimate Soil Moisture ~~~~~~~~~~~~~")
    ###############################################################################
    #                       Constants                                             #
    ###############################################################################
    print("Read in constants...")
    lw = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'LW'].item()
    lw = float(lw)
    soc = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'SOC'].item()
    soc = float(soc)
    try:
        bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD'].item()
        bd = float(bd)
        if math.isnan(bd):
            print("BD is nan value, using ISRIC data instead.")
            bd = meta.loc[(meta.COUNTRY == country) & (
                meta.SITENUM == sitenum), 'BD_ISRIC'].item()
            bd = float(bd)
    except:
        print("Couldn't find local bulk density data, using ISRIC data instead.")
        bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD_ISRIC'].item()
        bd = float(bd)
    print("BD is "+str(bd))
    N0 = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'N0'].item()
    N0 = int(N0)

    try:
        sm_max = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'SM_MAX'].item()
        sm_max = float(sm_max)
        if math.isnan(sm_max):
            print("Couldn't find SM_MAX in metadata. Creating value from bulk density data")
            sm_max = (1-(bd/(float(nld['density']))))
    except:
        print("Couldn't find SM_MAX in metadata. Creating value from bulk density data")
        sm_max = (1-(bd/(float(nld['density']))))
    # convert SOC to water equivelant (see Hawdon et al., 2014)
    soc = soc * 0.556
    hveg = 0  # Set to 0 to remove as data avilability low and impact low
    sm_min = 0  # Cannot have less than zero
    print("Done")
    ###############################################################################
    #                       Import Data                                           #
    ###############################################################################
    print("Calculating soil moisture along with estimated error...")
    df = pd.read_csv(nld['defaultdir']+"/data/crns_data/final/" +
                     country+"_SITE_"+sitenum+"_final.txt", sep="\t")
    df = df.replace(int(nld['noval']), np.nan)

    # Create MOD count to min and max of error
    df['MOD_CORR_PLUS'] = df['MOD_CORR'] + df['MOD_ERR']
    df['MOD_CORR_MINUS'] = df['MOD_CORR'] - df['MOD_ERR']
    
    if theta_method == "desilets":
        # Calculate soil moisture - including min and max error
        df['SM'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR'], N0, lw,
                                                soc), axis=1)
        df['SM'] = df['SM']
        df['SM_RAW'] = df['SM']

        df['SM_PLUS_ERR'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_MINUS'], N0, lw,
                                                            soc), axis=1)  # Find error (inverse relationship so use MOD minus for soil moisture positive Error)
        df['SM_PLUS_ERR'] = df['SM_PLUS_ERR']
        df['SM_PLUS_ERR'] = abs(df['SM_PLUS_ERR'] - df['SM'])

        df['SM_MINUS_ERR'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_PLUS'], N0, lw,
                                                            soc), axis=1)
        df['SM_MINUS_ERR'] = df['SM_MINUS_ERR']
        df['SM_MINUS_ERR'] = abs(df['SM_MINUS_ERR'] - df['SM'])
    elif theta_method == "kohli":
        df['SM'] = df.apply(lambda row: theta_kohli(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR'], N0, lw,
                                                soc), axis=1)
        df['SM'] = df['SM']
        df['SM_RAW'] = df['SM']

        df['SM_PLUS_ERR'] = df.apply(lambda row: theta_kohli(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_MINUS'], N0, lw,
                                                            soc), axis=1)  # Find error (inverse relationship so use MOD minus for soil moisture positive Error)
        df['SM_PLUS_ERR'] = df['SM_PLUS_ERR']
        df['SM_PLUS_ERR'] = abs(df['SM_PLUS_ERR'] - df['SM'])

        df['SM_MINUS_ERR'] = df.apply(lambda row: theta_kohli(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_PLUS'], N0, lw,
                                                            soc), axis=1)
        df['SM_MINUS_ERR'] = df['SM_MINUS_ERR']
        df['SM_MINUS_ERR'] = abs(df['SM_MINUS_ERR'] - df['SM'])        
    
    # Remove values above or below max and min vols
    df.loc[df['SM'] < sm_min, 'SM'] = 0
    df.loc[df['SM'] > sm_max, 'SM'] = sm_max

    df.loc[df['SM_PLUS_ERR'] < sm_min, 'SM_PLUS_ERR'] = 0
    df.loc[df['SM_PLUS_ERR'] > sm_max, 'SM_PLUS_ERR'] = sm_max

    df.loc[df['SM_MINUS_ERR'] < sm_min, 'SM_MINUS_ERR'] = 0
    df.loc[df['SM_MINUS_ERR'] > sm_max, 'SM_MINUS_ERR'] = sm_max
    print("Done")

    #df['SM_ERROR'] = (df['SM_PLUS_ERR'] - df['SM_MINUS_ERR'])/2
    
    # Take 12 hour average
    print("Averaging and writing table...")
    df['SM_12h'] = df['SM'].rolling(int(nld['smwindow']), min_periods=6).mean()

    #!!! df['SM_12h_SG'] = savgol_filter(df['SM'], 13, 4)#Cannot be used on data with nan values - consider another method?

    # Depth calcs - use new Schron style. Depth is given considering radius and bd
    df['rs10m'] = df.apply(lambda row: rscaled(
        10, row['PRESS'], hveg, (row['SM'])), axis=1)
    df['rs75m'] = df.apply(lambda row: rscaled(
        75, row['PRESS'], hveg, (row['SM'])), axis=1)
    df['rs150m'] = df.apply(lambda row: rscaled(
        150, row['PRESS'], hveg, (row['SM'])), axis=1)

    df['D86_10m'] = df.apply(lambda row: D86(
        row['rs10m'], bd, (row['SM'])), axis=1)
    df['D86_75m'] = df.apply(lambda row: D86(
        row['rs75m'], bd, (row['SM'])), axis=1)
    df['D86_150m'] = df.apply(lambda row: D86(
        row['rs150m'], bd, (row['SM'])), axis=1)
    df['D86avg'] = (df['D86_10m'] + df['D86_75m'] + df['D86_150m']) / 3
    df['D86avg_12h'] = df['D86avg'].rolling(window=int(nld['smwindow']), min_periods=6).mean()


    if agg24 == True:
        #read in data
        df24 = pd.read_csv(nld['defaultdir']+"/data/crns_data/final/" +
                     country+"_SITE_"+sitenum+"_final.txt", sep="\t")
        df24 = df24.replace(int(nld['noval']), np.nan)
            # Error is the ((standard deviation) / MOD)*MODCORR
        df24['DT'] = pd.to_datetime(df24['DT'])
        df24 = df24.set_index(df24['DT'])

        #mean sample rest
        # Missing obs will affect avg - take avg and multiply by 24 hours.
        # Create a measure of missing vals
        df24['MOD_OBS_IN_DAY'] = df24.apply(lambda row: checkdata(row['MOD']),axis=1)
        df24['RAIN_OBS_IN_DAY'] = df24.apply(lambda row: checkdata(row['RAIN']),axis=1)
        df24 = df24.resample('D').mean()
        df24['MOD'] = df24['MOD']*24
        df24['MOD_CORR'] = df24['MOD_CORR']*24
        df24['RAIN'] = df24['RAIN']*24

        #calc err
        df24['MOD_ERR'] = (np.sqrt(df24['MOD'])/df24['MOD']) * df24['MOD_CORR']
        df24['MOD_ERR'] = df24['MOD_ERR'].apply(np.floor)
        df24['MOD_CORR_PLUS'] = df24['MOD_CORR'] + df24['MOD_ERR']
        df24['MOD_CORR_MINUS'] = df24['MOD_CORR'] - df24['MOD_ERR']

        df24['SM'] = df24.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR'], N0*24, lw,
                                                soc), axis=1)
        df24['SM'] = df24['SM']
        df24['SM_RAW'] = df24['SM']

        df24['SM_PLUS_ERR'] = df24.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_MINUS'], N0*24, lw,
                                                            soc), axis=1)  # Find error (inverse relationship so use MOD minus for soil moisture positive Error)
        df24['SM_PLUS_ERR'] = df24['SM_PLUS_ERR']
        df24['SM_PLUS_ERR'] = abs(df24['SM_PLUS_ERR'] - df24['SM'])

        df24['SM_MINUS_ERR'] = df24.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_PLUS'], N0*24, lw,
                                                            soc), axis=1)
        df24['SM_MINUS_ERR'] = df24['SM_MINUS_ERR']
        df24['SM_MINUS_ERR'] = abs(df24['SM_MINUS_ERR'] - df24['SM'])

        df24.loc[df24['SM'] < sm_min, 'SM'] = 0
        df24.loc[df24['SM'] > sm_max, 'SM'] = sm_max

        df24.loc[df24['SM_PLUS_ERR'] < sm_min, 'SM_PLUS_ERR'] = 0
        df24.loc[df24['SM_PLUS_ERR'] > sm_max, 'SM_PLUS_ERR'] = sm_max

        df24.loc[df24['SM_MINUS_ERR'] < sm_min, 'SM_MINUS_ERR'] = 0
        df24.loc[df24['SM_MINUS_ERR'] > sm_max, 'SM_MINUS_ERR'] = sm_max

        df24.fillna(int(nld['noval']), inplace=True)
        df24 = df24.round(3)
        df24 = df24.reset_index()
        df24.to_csv(nld['defaultdir'] + "/data/crns_data/final/"+country+"_SITE_"+sitenum+"_final_24agg.txt",
              header=True, index=False, sep="\t", mode="w") 

    # Replace nans with -999
    df.fillna(int(nld['noval']), inplace=True)
    df = df.round(3)
    df = df.drop(['rs10m', 'rs75m', 'rs150m', 'D86_10m',
                  'D86_75m', 'D86_150m', 'MOD_CORR_PLUS', 'MOD_CORR_MINUS'], axis=1)  # ,
    #     'MOD_CORR_PLUS', 'MOD_CORR_MINUS', 'SM_PLUS_ERR', 'SM_MINUS_ERR'], axis=1)

    df.to_csv(nld['defaultdir'] + "/data/crns_data/final/"+country+"_SITE_"+sitenum+"_final.txt",
              header=True, index=False, sep="\t", mode="w")

    # Add the graphical function to output timeseries
    colourts(country, sitenum, yearlysmfig)

    print("Done")
    return df
