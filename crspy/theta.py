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


def theta_calc(a0, a1, a2, bd, N, N0, lw, wsom):
    """theta_calc standard theta calculation

    Parameters
    ----------
    a0 : float
        constant
    a1 : float
        constant
    a2 : float
        constant
    bd : float
        bulk density e.g. 1.4 g/cm3
    N : int
        Neutron count (corrected)
    N0 : int
        N0 number
    lw : float
        lattice water - decimal percent e.g. 0.002
    wsom : float
        soil organic carbon - decimal percent e.g, 0.02


    """
    return (((a0)/((N/N0)-a1))-(a2)-lw-wsom)*bd


def thetaprocess(df, meta, country, sitenum, yearlysmfig=True, nld=nld):
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
    soc = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'SOC'].item()
    try:
        bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD'].item()
        if math.isnan(bd):
            print("BD is nan value, using ISRIC data instead.")
            bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD_ISRIC'].item()
    except:
        print("Couldn't find local bulk density data, using ISRIC data instead.")
        bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD_ISRIC'].item()
    print("BD is "+str(bd))
    N0 = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'N0'].item()

    try:
        sm_max = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'SM_MAX'].item()
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

    # Calculate soil moisture - including min and max error
    df['SM'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR'], N0, lw,
                                               soc), axis=1)
    df['SM'] = df['SM']

    df['SM_PLUS_ERR'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_MINUS'], N0, lw,
                                                        soc), axis=1)  # Find error (inverse relationship so use MOD minus for soil moisture positive Error)
    df['SM_PLUS_ERR'] = df['SM_PLUS_ERR']
    df['SM_PLUS_ERR'] = abs(df['SM_PLUS_ERR'] - df['SM'])

    df['SM_MINUS_ERR'] = df.apply(lambda row: theta_calc(float(nld['a0']), float(nld['a1']), float(nld['a2']), bd, row['MOD_CORR_PLUS'], N0, lw,
                                                         soc), axis=1)
    df['SM_MINUS_ERR'] = df['SM_MINUS_ERR']
    df['SM_MINUS_ERR'] = abs(df['SM_MINUS_ERR'] - df['SM'])
    
    # Remove values above or below max and min volsm
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

    # Write a "clean" file that is just corrected soil moisture and depth of measurement
    # removed "SM_12h_SG" for now
    smclean = pd.DataFrame(
        df, columns=["DT", "SM", "D86avg", "SM_12h",  "D86avg_12h"])
    smclean = smclean.replace(np.nan, int(nld['noval']))
    smclean = smclean.round(3)
    smclean.to_csv(nld['defaultdir'] + "/data/crns_data/simple/"+country+"_SITE_" + sitenum+"_simple.txt",
                   header=True, index=False, sep="\t", mode='w')

    # Replace nans with -999
    df.fillna(int(nld['noval']), inplace=True)
    df = df.round(3)
    df = df.drop(['rs10m', 'rs75m', 'rs150m', 'D86_10m',
                  'D86_75m', 'D86_150m', 'MOD_CORR_PLUS', 'MOD_CORR_MINUS'], axis=1)  # ,
    #     'MOD_CORR_PLUS', 'MOD_CORR_MINUS', 'SM_PLUS_ERR', 'SM_MINUS_ERR'], axis=1)

    df.to_csv(nld['defaultdir'] + "/data/crns_data/FINAL/"+country+"_SITE_"+sitenum+"_final.txt",
              header=True, index=False, sep="\t", mode="w")

    # Add the graphical function to output timeseries
    colourts(country, sitenum, yearlysmfig)

    print("Done")
    return df
