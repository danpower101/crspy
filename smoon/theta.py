"""
Created on Wed Aug 28 15:20:35 2019

@author: Daniel Power
Email: daniel.power@bristol.ac.uk


"""

from name_list import nld
import os
os.chdir(nld['defaultdir'])
import pandas as pd
from smoon import n0_calibration as n0f
import numpy as np
from scipy.signal import savgol_filter 
###############################################################################
#                       Add the sitenum/country                               #
###############################################################################
"""


"""
def theta(a0, a1, a2, ps, N, N0, lw, wsom):
    """
    The standard calculation to give an estimate of soil moisture in g cm^3
    """
    return (((a0*ps)/((N/N0)-a1))-(a2*ps)-lw-wsom)

def thetaprocess(df, meta, country, sitenum):
    """
    Takes the dataframe provided by previous steps and uses the theta calculations
    to give an estimate of soil moisture. 
    
    Constants are taken from meta data which is identified using the "country" and "sitenum"
    inputs. 
    
    Realistic values are provided by constraining soil moisture estimates to physically possible values.
        i.e. Nothing below 0 and max values based on porosity at site.
        
    Provides an estimated depth of measurement using the D86 function from Shcron et al., (2017)
    
    Gives running averages of measurements using a 12 hour window. To handle missing 
    data a minimum of 6 hours of data per 12 hour window is required, otherwise one
    missing hour could lead to large gaps in 12 hour means. 
    
    Savitsky-Golay (SG filter) is also provided using a 12 hour window. 
    """
    
    ###############################################################################
    #                       Constants                                             #
    ###############################################################################
    lw = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'LW'].item()
    soc = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'SOC'].item()
    bd = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'BD'].item()
    N0 = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'NEW_N0'].item()
    hveg = 0 # Set to 0 to remove as data avilability low and impact low
    sm_min = 0 # Cannot have less than none
    sm_max = (1-(bd/(nld['density'])))*100 # Create a max realistic vol sm (NEED TO CONSIDER NUMBER FOR DENSITY)!!!
    
    ###############################################################################
    #                       Import Data                                           #
    ###############################################################################
    
    df = pd.read_csv(nld['defaultdir']+"data/crns_data/level1/"+country+"_SITE_"+sitenum+"_LVL1.txt", sep="\t")
    
    # Calculate soil moisture 
    df['SM'] = df.apply(lambda row: theta(nld['a0'], nld['a1'], nld['a2'], bd, row['MODCORR'], N0, lw,
      soc), axis=1)
    df['SM'] = df['SM']*100
    
    # Remove values above or below max and min volsm
    df.loc[df['SM'] < sm_min, 'SM'] = 0   
    df.loc[df['SM'] > sm_max, 'SM'] = sm_max    
    
    # Take 12 hour average
    df['SM_12h'] = df['SM'].rolling(nld['smwindow'], min_periods=6).mean() 
    df['SM_12h_SG'] = savgol_filter(df['SM'], 13, 4)

    # Depth calcs - use new Schron style. Depth is given considering radius and bd
    df['rs10m'] = df.apply(lambda row: n0f.rscaled(10, row['PRESS'], hveg, (row['SM']/100)), axis=1)
    df['rs75m'] = df.apply(lambda row: n0f.rscaled(75, row['PRESS'], hveg, (row['SM']/100)), axis=1)
    df['rs150m'] = df.apply(lambda row: n0f.rscaled(150, row['PRESS'], hveg, (row['SM']/100)), axis=1)
    
    df['D86_10m'] = df.apply(lambda row: n0f.D86(row['rs10m'], bd, (row['SM']/100)), axis=1)
    df['D86_75m'] = df.apply(lambda row: n0f.D86(row['rs75m'], bd, (row['SM']/100)), axis=1)
    df['D86_150m'] = df.apply(lambda row: n0f.D86(row['rs150m'], bd, (row['SM']/100)), axis=1)
    df['D86avg'] = (df['D86_10m'] + df['D86_75m'] + df['D86_150m']) /3
    df['D86avg_12h'] = df['D86avg'].rolling(window=nld['smwindow']).mean() #!!! SG filter etc
    
    # Write a "clean" file that is just corrected soil moisture and depth of measurement
    smclean = pd.DataFrame(df, columns = [ "DT", "SM", "D86avg", "SM_12h", "SM_12h_SG", "D86avg_12h"])
    smclean = smclean.replace(np.nan, -999)
    smclean = smclean.round(3)
    smclean.to_csv(nld['defaultdir'] + "/data/crns_data/level2/"+country+"_SITE_" + sitenum+"_LVL2.txt",
          header=True, index=False, sep="\t", mode='w')
    
    
    # Write a more detailed analysis file
    df['SM_withoutcorrections'] = df.apply(lambda row: theta(nld['a0'], nld['a1'], nld['a2'], bd, row['MOD'], N0, lw,
      soc), axis=1)
    df['SM_withoutcorrections'] = df['SM_withoutcorrections']*100
    
    # Replace nans with -999
    df.fillna(-999, inplace=True)
    df = df.round(3)
    df = df.drop(['rs10m', 'rs75m', 'rs150m','D86_10m', 'D86_75m', 'D86_150m', 'CALIBCORR'], axis=1)
    
    return df, smclean
