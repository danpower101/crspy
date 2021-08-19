# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 17:17:33 2019
@author: Daniel Power
The below code is based on the work of Schron et al., (2017). This work established
a new weighting scheme to be applied in the calibration of Cosmic Ray Neutron Sensors.
The functions have been taken from the supplementary data.  
References:
    Schrön, M., Köhli, M., Scheiffele, L., Iwema, J., Bogena, H. R., Lv, L., Martini, E.,
    Baroni, G., Rosolem, R., Weimar, J., Mai, J., Cuntz, M., Rebmann, C., Oswald, S. E.,
    Dietrich, P., Schmidt, U., and Zacharias, S.: Improving calibration and validation 
    of cosmic-ray neutron sensors in the light of spatial sensitivity, 
    Hydrol. Earth Syst. Sci., 21, 5009–5030, https://doi.org/10.5194/hess-21-5009-2017, 2017. 
     
    
"""
# Load up the packages needed at the begining of the code
import pandas as pd  # Pandas for dataframe
import re
import os
import numpy as np
import math
import matplotlib.pyplot as plt
import warnings

# crspy funcs
from crspy.neutron_correction_funcs import pv, es, ea

# Brought in to stop warning around missing data
warnings.filterwarnings("ignore", category=RuntimeWarning)
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')

""" 
Functions from Shcron et al 2017
     
"""

def WrX(r, x, y):
    """WrX Radial Weighting function for point measurements taken within 5m of sensor

    Parameters
    ----------
    r : float
        rescaled distance from sensor (see rscaled function below)
    x : float
        Air Humidity from 0.1 to 0.50 in g/m^3
    y : float
        Soil Moisture from 0.02 to 0.50 in m^3/m^3
    """

    x00 = 3.7
    a00 = 8735
    a01 = 22.689
    a02 = 11720
    a03 = 0.00978
    a04 = 9306
    a05 = 0.003632
    a10 = 2.7925e-002
    a11 = 6.6577
    a12 = 0.028544
    a13 = 0.002455
    a14 = 6.851e-005
    a15 = 12.2755
    a20 = 247970
    a21 = 23.289
    a22 = 374655
    a23 = 0.00191
    a24 = 258552
    a30 = 5.4818e-002
    a31 = 21.032
    a32 = 0.6373
    a33 = 0.0791
    a34 = 5.425e-004

    x0 = x00
    A0 = (a00*(1+a03*x)*np.exp(-a01*y)+a02*(1+a05*x)-a04*y)
    A1 = ((-a10+a14*x)*np.exp(-a11*y/(1+a15*y))+a12)*(1+x*a13)
    A2 = (a20*(1+a23*x)*np.exp(-a21*y)+a22-a24*y)
    A3 = a30*np.exp(-a31*y)+a32-a33*y+a34*x

    return((A0*(np.exp(-A1*r))+A2*np.exp(-A3*r))*(1-np.exp(-x0*r)))


def WrA(r, x, y):
    """WrA Radial Weighting function for point measurements taken within 50m of sensor

    Parameters
    ----------
    r : [type]
        [description]
    x : [type]
        [description]
    y : [type]
        [description]
    """

    a00 = 8735
    a01 = 22.689
    a02 = 11720
    a03 = 0.00978
    a04 = 9306
    a05 = 0.003632
    a10 = 2.7925e-002
    a11 = 6.6577
    a12 = 0.028544
    a13 = 0.002455
    a14 = 6.851e-005
    a15 = 12.2755
    a20 = 247970
    a21 = 23.289
    a22 = 374655
    a23 = 0.00191
    a24 = 258552
    a30 = 5.4818e-002
    a31 = 21.032
    a32 = 0.6373
    a33 = 0.0791
    a34 = 5.425e-004

    A0 = (a00*(1+a03*x)*np.exp(-a01*y)+a02*(1+a05*x)-a04*y)
    A1 = ((-a10+a14*x)*np.exp(-a11*y/(1+a15*y))+a12)*(1+x*a13)
    A2 = (a20*(1+a23*x)*np.exp(-a21*y)+a22-a24*y)
    A3 = a30*np.exp(-a31*y)+a32-a33*y+a34*x

    return(A0*(np.exp(-A1*r))+A2*np.exp(-A3*r))


def WrB(r, x, y):
    """WrB Radial Weighting function for point measurements taken over 50m of sensor

    Parameters
    ----------
    r : float
        rescaled distance from sensor (see rscaled function below)
    x : float
        Air Humidity from 0.1 to 0.50 in g/m^3
    y : float
        Soil Moisture from 0.02 to 0.50 in m^3/m^3
    """
    b00 = 39006
    b01 = 15002337
    b02 = 2009.24
    b03 = 0.01181
    b04 = 3.146
    b05 = 16.7417
    b06 = 3727
    b10 = 6.031e-005
    b11 = 98.5
    b12 = 0.0013826
    b20 = 11747
    b21 = 55.033
    b22 = 4521
    b23 = 0.01998
    b24 = 0.00604
    b25 = 3347.4
    b26 = 0.00475
    b30 = 1.543e-002
    b31 = 13.29
    b32 = 1.807e-002
    b33 = 0.0011
    b34 = 8.81e-005
    b35 = 0.0405
    b36 = 26.74

    B0 = (b00-b01/(b02*y+x-0.13))*(b03-y)*np.exp(-b04*y)-b05*x*y+b06
    B1 = b10*(x+b11)+b12*y
    B2 = (b20*(1-b26*x)*np.exp(-b21*y*(1-x*b24))+b22-b25*y)*(2+x*b23)
    B3 = ((-b30+b34*x)*np.exp(-b31*y/(1+b35*x+b36*y))+b32)*(2+x*b33)

    return(B0*(np.exp(-B1*r))+B2*np.exp(-B3*r))


# Vertical

def D86(r, bd, y):
    """D86 Calculates the depth of sensor measurement (taken as the depth from which
    86% of neutrons originate)

    Parameters
    ----------
    r : float, int
        radial distance from sensor (m)
    bd : float
        bulk density (g/cm^3)
    y : float
        Soil Moisture from 0.02 to 0.50 in m^3/m^3
    """

    return(1/bd*(8.321+0.14249*(0.96655+np.exp(-0.01*r))*(20+y)/(0.0429+y)))


def Wd(d, r, bd, y):
    """Wd Weighting function to be applied on samples to calculate weighted impact of 
    soil samples based on depth.

    Parameters
    ----------
    d : float
        depth of sample (cm)
    r : float,int
        radial distance from sensor (m)
    bd : float
        bulk density (g/cm^3)
    y : float
        Soil Moisture from 0.02 to 0.50 in m^3/m^3
    """

    return(np.exp(-2*d/D86(r, bd, y)))


# Rescaled distance
def rscaled(r, p, Hveg, y):
    """rscaled rescales the radius based on below parameters

    Parameters
    ----------
    r : float
        radius from sensor (m)
    p : float
        pressure at site (mb)
    Hveg : float
        height of vegetation during calibration period (m)
    y : float
        Soil Moisture from 0.02 to 0.50 in m^3/m^3
    """
    Fp = 0.4922/(0.86-np.exp(-p/1013.25))
    Fveg = 1-0.17*(1-np.exp(-0.41*Hveg))*(1+np.exp(-9.25*y))
    return(r / Fp / Fveg)


def n0_calib(meta, country, sitenum, defineaccuracy, nld=nld):
    """n0_calib the full calibration process

    Parameters
    ----------
    meta : dataframe
        metadata dataframe
    country : str
        country of the site e.g. "USA"`
    sitenum : str
        sitenum of the site "e.g.
    defineaccuracy : float
        accuracy that is desired usually 0.01
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']

    print("~~~~~~~~~~~~~ N0 Calibration ~~~~~~~~~~~~~")
    # Bulk Density (bd), Site Name, Soil Organic Carbon (soc) and lattice water (lw) taken from meta data
    # Here using average of BD given in calibration data
    bd = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'BD'].item()
    bdunavailable = False
    if math.isnan(bd):
        bd = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'BD_ISRIC'].item()  # Use ISRIC data if unavailable
        bdunavailable = True
    sitename = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'SITE_NAME'].item()
    soc = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'SOC'].item()
    lw = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'LW'].item()
    Hveg = 0  # Hveg not used due to lack of reliable data and small impact.

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    First some housekeeping - create folders for writing to later on
    """
    print("Creating Folders...")
    # Create a folder name for reports and tables unique to site
    uniquefolder = country + "_" + str(sitenum)
    # Change wd to folder for N0 recalib
    os.chdir(nld['defaultdir'] + "/data/n0_calibration/")
    alreadyexist = os.path.exists(uniquefolder)  # Checks if the folder exists

    if alreadyexist == False:
        # Statement to manage writing a new folder or not depending on existance
        os.mkdir(uniquefolder)
    else:
        pass

    os.chdir(nld['defaultdir'])  # Change back to main wd
    print("Done")

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~ CALIBRATION DATA READ AND TIDY ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Read in the calibration data and do some tidying to it
    """
    print("Fetching calibration data...")
    # Read in Calibration data for Site_11
    df = pd.read_csv(
        nld['defaultdir'] + "/data/calibration_data/Calib_"+country+"_SITE_" + sitenum+".csv")
    COSMOScols = ['label:number', 'type:text', 'uri:url', 'change:text',
                  'changedItem:text', 'modified:text', 'Depth_cm:number',
                  'Wet_total_g:number', 'Dry_total_g:number', 'Tare_g:number',
                  'Wet_soil_g:number', 'Dry_soil_g:number', 'Soil_water_w_%:number',
                  'Bulk_density:number', 'Soil_water_v_%:number', 'date:text',
                  'Tin_Label:text', 'Location:text', 'Volumetric:text']
    cols = list(df.columns)

    # Check to see if calibration is in COSMOS format - if so rename
    if cols == COSMOScols:
        df.columns = ("LABEL", "TYPE", "URL", "CHANGE", "CHANGE2", "MODIFIED", "DEPTH", "WET_TOTAL", "DRY_TOTAL",
                      "TARE", "WET_SOIL", "DRY_SOIL", "SWW", "BD", "SWV", "DATE",
                      "TIN_LABEL", "LOC", "VOLUMETRIC")
        df['LOC'] = df['LOC'].astype(str)  # Dtype into string

    df['DATE'] = pd.to_datetime(
        df['DATE'], format=nld['cdtformat'])  # Dtype into DATE
    # Remove the hour part as  interested in DATE here
    df['DATE'] = df['DATE'].dt.date

    unidate = df.DATE.unique()  # Make object of unique dates (calib dates)
    print("Unique calibration dates found: "+str(unidate))
    print("Done")

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~ FINDING RADIAL DISTANCES OF MEASUREMENTS ~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Using the LOC column which combines directional heading and radial
    distance from sensor. It splits this column to give raidal distance
    in metres.
    
    Try/except introduced as sometimes direction isn't available.
    """
    if "LOC" in df.columns:
        # Create a column with radius from sensor in it from LOC
        radius = []  # Placeholder
        direction = []  # Placeholder
        for row in df['LOC']:
            # dir = letters & rad = numbers
            m = re.match(r"(?P<dir>[a-zA-Z]+)(?P<rad>.+)$", row)
            try:
                direction.append(m.group('dir'))
                # Append to the above placeholders
                radius.append(m.group('rad'))
            except AttributeError:
                direction.append("None")
                radius.append(row)
        df['LOC_dir'] = direction
        df['LOC_rad'] = radius  # Attach to the dataframe

        # Some data had "?" in place of LOC. Can't use as no idea on where sample from.
        df = df[df['LOC_rad'].apply(lambda x: x.isnumeric())]
        df['LOC_rad'] = df['LOC_rad'].astype(float)
    else:
        df['LOC_rad'] = df['LOC_rad'].astype(float)  # dtype is float

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~ PROVIDE A SINGLE NUMBER FOR DEPTH ~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Calibration data has the depth given as a range in meters. For easier
    handling this is converted into an average depth of the range.
    
    """

    print("Collecting additional data...")

    if "DEPTH_AVG" not in df.columns:
        # Turn depth range into a point value by taking average of the range
        depth = df["DEPTH"].str.split(" ", n=1, expand=True)
        # Splits the column using the '-' between the depths
        depth = depth[0].str.split("-", n=1, expand=True)
        depth['0'] = depth[0].astype(float)
        depth['1'] = depth[1].astype(float)
        # Finds the average depth of range
        df['DEPTH_RANGE'] = (depth['1'] - depth['0'])
        df['DEPTH_AVG'] = depth['0'] + (df['DEPTH_RANGE']/2)
    else:
        df['DEPTH_AVG'] = df['DEPTH_AVG'].astype(float)

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~ SEPERATE TABLES FOR EACH CALIB DAY ~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    It will look at the number of unique days identified above. It will then create
    seperate tables for each calibration day. 
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    """
    # Numdays is a number from 1 to n that defines how many calibration days there are.
    numdays = len(unidate)

    # Dict that contains a df for each unique calibration day.
    dfCalib = dict()
    for i in range(numdays):
        dfCalib[i] = df.loc[df['DATE'] == unidate[i]]

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~ AVERAGE PRESSURE FOR EACH CALIB DAY ~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    We need average pressure for the functions further down the script. This will 
    find the average pressure - obtained from the level 1 data
    """
    # ERROR - if lvl1['DATE'] = NA check formatting (line 163)
    lvl1 = pd.read_csv(nld['defaultdir'] + "/data/crns_data/tidy/" +
                       country+"_SITE_" + sitenum+"_TIDY.txt", sep="\t")
    lvl1['DATE'] = pd.to_datetime(
        lvl1['DT'], format='%Y/%m/%d')  # Use correct formatting
    lvl1['DATE'] = lvl1['DATE'].dt.date     # Remove the time portion
    if lvl1['E_RH'].mean() == int(nld['noval']):
        isrh = False                         #Check if external RH is available
    else:
        isrh = True
    lvl1[lvl1 == int(nld['noval'])] = np.nan

    # Creates dictionary of dfs for calibration days found
    dflvl1Days = dict()
    for i in range(numdays):
        dflvl1Days[i] = lvl1.loc[lvl1['DATE'] == unidate[i]]

    # Create a dict of avg pressure for each Calibday
    avgP = dict()
    for i in range(len(dflvl1Days)):
        tmp = pd.DataFrame.from_dict(dflvl1Days[i])
        tmp = tmp[(tmp['DT'] > str(unidate[i])+' 16:00:00') & (tmp['DT']
                                                               <= str(unidate[i])+' 23:00:00')]  # COSMOS time of Calib
        check = float(np.nanmean(tmp['PRESS'], axis=0))

        if np.isnan(check):
            tmp = pd.DataFrame.from_dict(dflvl1Days[i])
            avgP[i] = float(np.nanmean(tmp['PRESS'], axis=0))
        else:
            avgP[i] = check
        # Very few sites had no data at time of COSMOS calib - if thats the case use day average

    avgT = dict()
    for i in range(len(dflvl1Days)):
        tmp = pd.DataFrame.from_dict(dflvl1Days[i])
        tmp = tmp[(tmp['DT'] > str(unidate[i])+' 16:00:00') & (tmp['DT']
                                                               <= str(unidate[i])+' 23:00:00')]  # COSMOS time of Calib
        check = float(np.nanmean(tmp['TEMP'], axis=0))
        # Very few sites had no data at time of COSMOS calib - if thats the case use day average
        if np.isnan(check):
            tmp = pd.DataFrame.from_dict(dflvl1Days[i])
            avgT[i] = float(np.nanmean(tmp['TEMP'], axis=0))
        else:
            avgT[i] = check

    if isrh:
        avgRH = dict()
        for i in range(len(dflvl1Days)):
            tmp = pd.DataFrame.from_dict(dflvl1Days[i])
            tmp = tmp[(tmp['DT'] > str(unidate[i])+' 16:00:00') & (tmp['DT']
                                                                <= str(unidate[i])+' 23:00:00')]  # COSMOS time of Calib
            check = float(np.nanmean(tmp['E_RH'], axis=0))
            # Very few sites had no data at time of COSMOS calib - if thats the case use day average
            if np.isnan(check):
                tmp = pd.DataFrame.from_dict(dflvl1Days[i])
                avgRH[i] = float(np.nanmean(tmp['E_RH'], axis=0))
            else:
                avgRH[i] = check
        
    if isrh == False:
        avgVP = dict()
        for i in range(len(dflvl1Days)):
            tmp = pd.DataFrame.from_dict(dflvl1Days[i])
            tmp = tmp[(tmp['DT'] > str(unidate[i])+' 16:00:00') & (tmp['DT']
                                                                <= str(unidate[i])+' 23:00:00')]  # COSMOS time of Calib
            check = float(np.nanmean(tmp['VP'], axis=0))
            # Very few sites had no data at time of COSMOS calib - if thats the case use day average
            if np.isnan(check):
                tmp = pd.DataFrame.from_dict(dflvl1Days[i])
                avgVP[i] = float(np.nanmean(tmp['VP']))
            else:
                avgVP[i] = check
    print("Done")
    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~ THE BIG ITERATIVE LOOP - CALCULATE WEIGHTED THETA ~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Below is the main loop that will iterate through the process oultined by 
    Schron et al., (2017). It iterate the weighting procedure until the defined
    accuracy is achieved. It will then repeat for as many calibration days there
    are.
    """

    AvgTheta = dict()  # Create a dictionary to place the AvgTheta into

    for i in range(len(dflvl1Days)):  # for i in number of calib days...

        print("Calibrating to day "+str(i+1)+"...")
        # Assign first calib day df to df1
        df1 = pd.DataFrame.from_dict(dfCalib[i])
        if df1['SWV'].mean() > 1:
            print("crspy has detected that your volumetric soil water units (in the calibration data) are not in decimal format and so has divided them by 100. If this is incorrect please adjust the units and reprocess your data")
            # added to convert - handled with message plus calc
            df1['SWV'] = df1['SWV']/100

        CalibTheta = df1['SWV'].mean()           # Unweighted mean of SWV
        # Assign accuracy as 1 to be compared to in while loop below
        Accuracy = 1

        # COSMOS data needs some processing to get profiles - check if already available
        if "PROFILE" not in df1.columns:
            # Create a profile tag for each profile
            profiles = df1.LOC.unique()             # Find unique profiles
            # Defines the number of profiles
            numprof = len(profiles)

            # Following mini-loop will append an integer value for each profile
            pfnum = []
            for row in df1['LOC']:
                for j in range(numprof):
                    if row == profiles[j, ]:
                        pfnum.append(j+1)
            df1['PROFILE'] = pfnum

            # Now loop the iteration until the defined accuracy is achieved
        while Accuracy > defineaccuracy:
            # Initial Theta
            thetainitial = CalibTheta  # Save a copy for comparison
            """
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~~ DEPTH WEIGHTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            According to Schron et al., (2017) the first thing to do is find the 
            weighted average for each profile. This is done 
            """
            # Rescale the radius using rscaled function
            df1['rscale'] = df1.apply(lambda row: rscaled(
                row['LOC_rad'], avgP[i], Hveg, thetainitial), axis=1)

            # Calculate the depth weighting for each layer
            df1['Wd'] = df1.apply(lambda row: Wd(
                row['DEPTH_AVG'], row['rscale'], bd, thetainitial), axis=1)
            df1['thetweight'] = df1['SWV'] * df1['Wd']

            # Create a table with the weighted average of each profile
            depthdf = df1.groupby('PROFILE', as_index=False)[
                'thetweight'].sum()
            temp = df1.groupby('PROFILE', as_index=False)['Wd'].sum()
            depthdf['Wd_tot'] = temp['Wd']
            depthdf['Profile_SWV_AVG'] = depthdf['thetweight'] / \
                depthdf['Wd_tot']
            dictprof = dict(zip(df1.PROFILE, df1.LOC_rad))
            dictprof2 = dict(zip(df1.PROFILE, df1.rscale))
            depthdf['Radius'] = depthdf['PROFILE'].map(dictprof)
            depthdf['rscale'] = depthdf['PROFILE'].map(dictprof2)
            """
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~ ABSOLUTE HUMIDITY CALULCATION ~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            Need to provide absolute air humidity for each calibration day. This will be 
            taken from data (vapour pressure and temperature) for the USA sites. 
            Using the pv function from hum_funcs.py this can be calculated by providing 
            vapour pressure and temperature.
            """
            if isrh == True:
                day1temp = avgT[i]
                day1rh = avgRH[i]

                day1es = es(day1temp)
                day1es = day1es*100 # convert to Pa
                day1ea = ea(day1es, day1rh)
                day1hum = pv(day1ea, day1temp)
                day1hum = day1hum * 1000

            else:
                day1temp = avgT[i]
                day1vp = avgVP[i]
                
                # Calculate absolute humidity (output will be kg m-3).
                day1hum = pv(day1vp, day1temp)
                # Multiply by 1000 to convert to g m-3 which is used by functions
                day1hum = day1hum * 1000

            # Need to add value to each row for .loc application
            depthdf['day1hum'] = day1hum
            depthdf['TAVG'] = day1temp
            depthdf['Wr'] = "NaN"  # set up column
            """
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~ RADIAL WEIGHTING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            Once each profile has a depth averaged value, and we have the absolute
            humidity, we can begin to find the final weighted value of theta. Three
            different functions are utilised below depending on the distance from
            sensor.
            """
            # Below three lines applies WrN function based on radius of the measurement
            depthdf.loc[depthdf['Radius'] > 50, 'Wr'] = WrB(
                depthdf.rscale, depthdf.day1hum, (depthdf.TAVG / 100))
            depthdf.loc[(depthdf['Radius'] > 5) & (depthdf['Radius'] <= 50), 'Wr'] = WrA(
                depthdf.rscale, depthdf.day1hum, (depthdf.TAVG / 100))
            depthdf.loc[depthdf['Radius'] <= 5, 'Wr'] = WrX(
                depthdf.rscale, depthdf.day1hum, (depthdf.TAVG / 100))

            depthdf['RadWeight'] = depthdf['Profile_SWV_AVG'] * depthdf['Wr']

            FinalTheta = depthdf.sum()

            try:
                CalibTheta = FinalTheta['RadWeight'] / FinalTheta['Wr']
            except ZeroDivisionError:
                print("A zero division was attempted. This usually indicates missing data around the calibration date.")
            AvgTheta[i] = CalibTheta

            """
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~ WRITE TABLES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            The weighted tables are written to a folder for checking later. This is
            to ensure that the code has worked as expected and now crazy values are
            found.
            """
            # Below code will write the tables into the unique folder for checking
            # They will overwrite each time
            os.chdir(nld['defaultdir'] + "/data/n0_calibration/" +
                     uniquefolder)  # Change wd
            depthdf.to_csv(country + '_SITE_'+sitenum +   # Write the radial table
                           '_RadiusWeighting' + str(unidate[i]) + '.csv', header=True, index=False,  mode='w')
            df1.to_csv(country + '_SITE_'+sitenum +          # Write the depth table
                       '_DepthWeighting' + str(unidate[i]) + '.csv', header=True, index=False,  mode='w')
            os.chdir(nld['defaultdir'])  # Change wd back

            Accuracy = abs((CalibTheta - thetainitial) /
                           thetainitial)  # Calculate new accuracy
        print("Done")

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~ OPTIMISED N0 CALCULATION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    We now check the optimal N0 value for this sensor. This is completed by iterating
    through calculations of soil moisture for each calibration date with the N0 value
    being replaced with values from 0 - 10,000. We can then see what the accuracy is
    for each possible N0 value. 
    
    To optimise across calibration days these accuracy values are then summed for each
    N0 value across the calibration days. The lowest error value is then taken as the 
    correct N0.
    
    """
    print("Finding Optimised N0......")
    tmp = pd.read_csv(nld['defaultdir'] + '/data/crns_data/level1/' +
                      country + '_SITE_'+sitenum+'_LVL1.txt', sep='\t')
    # Use correct formatting - MAY NEED CHANGING AGAIN DUE TO EXCEL
    tmp = tmp.replace(int(nld['noval']), np.nan)
    #n_max = tmp['MOD_CORR'].max()
    n_avg = int(np.nanmean(tmp['MOD_CORR']))

    print("Avg N is for the site is  "+str(n_avg))
    tmp['DATE'] = pd.to_datetime(tmp['DT'], format="%Y-%m-%d %H:%M:%S")
    tmp['DATE'] = tmp['DATE'].dt.date  # Remove the time portion to match above

    

    NeutCount = dict()  # Create a dict for appending time series readings for each calib day
    for i in range(numdays):  # Create a df for each day with the CRNS readings
        # Create a dictionary df of neutron time series data for each calibration day
        tmpneut = tmp.loc[tmp['DATE'] == unidate[i]]
        NeutCount[i] = tmpneut
        # Write a csv for the error for this calibration day
        os.chdir(nld['defaultdir'] + "/data/n0_calibration/" +
                 uniquefolder)  # Change wd to folder

        tmpneut.to_csv(country + '_SITE_'+sitenum+'_MOD_AVG_TABLE_' + str(unidate[i]) + '.csv',
                       header=True, index=False,  mode='w')
        os.chdir(nld['defaultdir'])  # Change back

    avgN = dict()
    for i in range(len(NeutCount)):
        # Find the daily mean neutron count for each calibration day
        tmp = pd.DataFrame.from_dict(NeutCount[i])
        tmp = tmp[(tmp['DT'] > str(unidate[i])+' 16:00:00') & (tmp['DT']
                                                               <= str(unidate[i])+' 23:00:00')]  # COSMOS time of Calib
        check = float(np.nanmean(tmp['MOD_CORR']))
       # Need another catch to stop errors with missing data
        if np.isnan(check):
            # Find the daily mean neutron count for each calibration day
            tmp = pd.DataFrame.from_dict(NeutCount[i])
            avgN[i] = float(np.nanmean(tmp['MOD_CORR']))
        else:
            avgN[i] = check

    RelerrDict = dict()
    with np.errstate(divide='ignore'):  # prevent divide by 0 error message
        for i in range(numdays):
            # Create a series of N0's to test from 0 to 10000
            N0 = pd.Series(range(n_avg, int(n_avg*2)))
            # Avg theta divided by 100 to be given as decimal
            vwc = AvgTheta[i]
            Nave = avgN[i]  # Taken as average for calibration period
            sm = pd.DataFrame(columns=['sm'])
            reler = pd.DataFrame(columns=['RelErr'])

            for j in range(len(N0)):

                sm.loc[j] = ((float(nld["a0"]) / ((Nave / N0.loc[j]) -
                                           float(nld["a1"]))) - float(nld["a2"]) - lw - soc) * bd
                tmp = sm.iat[j, 0]
                # Accuracy normalised to vwc
                reler.loc[j] = abs((sm.iat[j, 0] - vwc)/vwc)

            RelerrDict[i] = reler['RelErr']

            # Write a csv for the error for this calibration day
            os.chdir(nld['defaultdir'] + "/data/n0_calibration/" +
                     uniquefolder)  # Change wd to folder

            reler['N0'] = range(n_avg, int(n_avg*2))  # Add N0 for csv write

            reler.to_csv(country + '_SITE_'+sitenum+'_error_' + str(unidate[i]) + '.csv',
                         header=True, index=False,  mode='w')
            os.chdir(nld['defaultdir'])  # Change back

    """
                        N0 Optimisation
    
    Need to optimise N0 based on all calibration days. This is done by taking a total
    mea from all sites. e.g. when N0 = 2000, sum mea for each calibration day at N0=2000.
    
    This is then used as our error calculation so we minimise for that to give us N0.
    """

    totalerror = RelerrDict[0]         # Create a total error series
    # Range is number of calibration days - 1 (as already assigned day 1)
    for i in range(len(unidate)-1):
        # Create a tmp series of the next calibration day
        tmp = RelerrDict[i+1]
        # Sum these together for total mea (will continue until all days are summed)
        totalerror = totalerror+tmp

    minimum_error = min(totalerror)  # Find the minimum error value and assign

    totalerror = totalerror.to_frame()
    totalerror['N0'] = range(n_avg, int(n_avg*2))
    # Create object that maintains the index value at min
    minindex = totalerror.loc[totalerror.RelErr == minimum_error]
    print("Done")
    # Show the minimum error value with the index valu. Index = N0
    print(minindex)

    N0 = minindex['N0'].item()

    meta.loc[(meta['SITENUM'] == sitenum) & (
        meta['COUNTRY'] == country), 'N0'] = N0

    meta.to_csv(nld['defaultdir'] + "/data/metadata.csv",
                header=True, index=False, mode='w')

    plt.plot(totalerror['RelErr'])
    plt.yscale('log')
    plt.xlabel('N0')
    plt.ylabel('Sum Relative Error (log scale)')
    plt.title('Sum Relative Error plot on log scale across all calibration days')
    plt.legend()
    os.chdir(nld['defaultdir'] + "/data/n0_calibration/" +
             uniquefolder)  # Change wd to folder
    plt.savefig("Relative_Error_Plot.png")
    os.chdir(nld['defaultdir'])
    plt.close()

    """
                            User Report
                            
    This report is going to outline all the variables and calculations that are used
    in the automated process. It is essential for the user to read through this and 
    identify if there is anything that seems incorrect.
    
    Examples:   Too many/few calibration days
                TempAvg is unrealistic
                Calibration Dates are incorrect
                Any values that appear beyond reasonable
                
    This should work correctly however mistakes are possible if, for example, the 
    data structure is wrong. This could cause knock on effects.
    
    """

    N0R = "The optimised N0 is calculated as: \nN0   |  Total Relative Error  \n" + \
        str(minindex)
    R1 = "The site calibrated was site number " + sitenum + \
        " in  " + str(country) + " and the name is " + sitename
    if bdunavailable == False:
        R2 = "The bulk density was " + str(bd)
    else:
        R2 = "The bulk density value wasn't available and so estimate of 1.43 was used"
   # R3 = "The vegetation height was " +str(Hveg)+ " (m)"
    R4 = "The user defined accuracy was "+str(defineaccuracy)
    R5 = "The soil organic carbon was "+str(soc) + " g/m^3"
    R6 = "The lattice water content was " + str(lw)
    R7 = "Unique calibration dates where on: \n" + str(unidate)
    RAvg = "Average neutron counts for each calib day where " + str(avgN)
    Rtheta = "The weighted field scale average of theta (from soil samples) was "+str(
        AvgTheta)
    R8 = "Please see the additional tables which hold calculations for each calibration date"

    # Make a folder for the site being processed
    os.chdir(nld['defaultdir'] + "/data/n0_calibration/" +
             uniquefolder)  # Change wd to folder

    # Write the user report file below
    f = open(country + "_"+sitenum+"_Report.txt", "w")
    f.write(N0R + '\n\n' + R1 + '\n' + R2 + '\n' + R4 + '\n' + R5 + '\n' + R6 + '\n' +
            '\n \n' + R7 + '\n\n' + RAvg + '\n \n' + Rtheta + '\n \n' + R8)
    f.close()

    # Write total error table
    totalerror = pd.DataFrame(totalerror)
    totalerror['N0'] = range(n_avg, int(n_avg*2))
    totalerror.to_csv(country + '_SITE_'+sitenum +
                      'totalerror.csv', header=True, index=False,  mode='w')

    os.chdir(nld['defaultdir'])  # Change back
    return meta, N0
