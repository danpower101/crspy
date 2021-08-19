# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 16:35:56 2020

@author: Dan Power

Collection for graphical representation of data. Ways to show data.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import seaborn as sns
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')

def colourts(country, sitenum, yearlysm, nld=nld):
    """
    This function will output a series of plots and figures that can demonstrate
    conditions of a site for easy viewing.
    
    PARAMETERS:
        country: string - country as in metadata
            e.g. "UK"
        sitenum: string - sitenumber as in metadata
            e.g. "101"
        yearlysm: boolean - if turned to true it will output yearly 
                            plots of soil moisture for more granular viewing
        nld : dictionary
            nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
            This will store variables such as the wd and other global vars

    """
    nld=nld['config']
    meta = pd.read_csv(nld['defaultdir'] + "/data/metadata.csv")
    meta['SITENUM'] = meta.SITENUM.map("{:03}".format) # Add leading zeros
    df = pd.read_csv(nld['defaultdir'] + "/data/crns_data/final/"+country+"_SITE_"+sitenum+"_final.txt", sep="\t")

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    First some housekeeping - create folders for writing to later on
    """
    print("Creating Folders...")
    uniquefolder = country + "_" + str(sitenum) # Create a folder name for reports and tables unique to site
    os.chdir(nld['defaultdir'] + "/data/figures/") # Change wd to folder for N0 recalib
    alreadyexist = os.path.exists(uniquefolder) # Checks if the folder exists
    
    if alreadyexist == False:
        os.mkdir(uniquefolder) # Statement to manage writing a new folder or not depending on existance
    else:
        pass
    
    os.chdir(nld['defaultdir']) # Change back to main wd
    print("Done")
    
    sitename = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'SITE_NAME'].item()
    df = pd.read_csv(nld['defaultdir'] + "/data/crns_data/final/"+country+"_SITE_"+sitenum+"_final.txt", sep="\t")
    ymax = df.SM_12h.max()
    ymaxplus = ymax*1.05
    df.loc[df.SM_12h == int(nld['noval']), "SM_12h"] = np.nan
    df.loc[df.MOD_CORR == int(nld['noval']), "MOD_CORR"] = np.nan
    sm = df['SM_12h']
    dtime = pd.to_datetime(df['DT'], format= "%Y-%m-%d %H:%M:%S") # Create dt series for using in fill_between
    lower_bound = 0
    
     #DATETIME INDEXED
    dfdt = df.set_index(dtime)
    
    # CREATE COLOUR PALLETE
    #from colour import Color
    #basecol = Color("brown")
    nsteps = 50
    colrange = sns.diverging_palette(29, 255, 85 ,47, n=nsteps, sep = 1, center="light")
    prcnt35 = math.ceil(len(colrange)*0.30)  # Apply to allow changes to n bins
    prcnt65 = math.ceil(len(colrange)*0.55)
    colrange2 = colrange[0:prcnt35] + colrange[prcnt65:nsteps] # Subtract the white center of the range
    
    # FIND STEPS
     # Find the max soil moisture to limit colour pallete + normalise it to nsteps
    steps = ymax/nsteps
    gradrange = list(np.arange(0,ymax, steps))  # Figure 100 steps between min and max water content
    
    
    #CREATE MOD_CORR PLOT
    fig, ax = plt.subplots(figsize=(10,2.5))
    ax.plot(dfdt['MOD_CORR'], lw=0.1, label="Neutron Counts - "+str(sitename)+", "+str(country), color='black')
    ax.set_title("Neutron Counts - "+str(sitename)+", "+str(country))
    ax.set_ylabel("Neutron Count")
    fig.savefig(nld['defaultdir']+"/data/figures/"+uniquefolder+"/MOD_CORR.png", dpi=250)

    
    #CREATE COLOUR TS PLOT
    fig, ax = plt.subplots(figsize=(15,3.75))
    
    ax.plot(dfdt['SM_12h'], lw=0.1, label='Soil Moisture Volumetric (cm$^3$/cm$^3$)', color='black')
    ax.set_ylabel("Soil Moisture - Volumetric (cm$^3$/cm$^3$)")
    ax.set_xlabel("Date")
    ax.set_title("Soil Moisture over time at "+str(sitename)+", "+str(country))
    
    ax.plot(dtime, sm, lw=0.1, label='Soil Moisture Volumetric (cm$^3$/cm$^3$)', color='black')
    ax.set_ylim(lower_bound, ymaxplus) # Xlim to below 0 to allow brown colour to show
    for i in range(len(colrange2)):
        ax.fill_between(dtime, lower_bound, sm, where=sm > gradrange[i], facecolor=colrange2[i],
                        alpha=0.2)
    fig.savefig(nld['defaultdir']+"/data/figures/"+uniquefolder+"/SM_all.png", dpi=250)


    
    if yearlysm == True:
        df['DT'] = pd.to_datetime(df['DT'])
        df['YEAR'] = df['DT'].dt.year
        years = df['YEAR'].unique()
        
        for year in years:
            tmp = df.loc[df['YEAR'] == year]
            tmp = tmp.set_index(tmp.DT)
            dtime=tmp['DT']
            sm = tmp['SM_12h']
            steps = ymax/nsteps
            gradrange = list(np.arange(0,ymax, steps))
            
            fig, ax = plt.subplots(figsize=(15,3.75))
            ax.plot(tmp['SM_12h'], lw=0.1, label='Soil Moisture Volumetric (cm$^3$/cm$^3$)', color='black')
            ax.set_ylabel("Soil Moisture - Volumetric (cm$^3$/cm$^3$)")
            ax.set_xlabel("Date")
            ax.set_title("Soil Moisture over the year "+str(year)+" at "+str(sitename)+", "+str(country))
            
            ax.plot(dtime, sm, lw=0.1, label='Soil Moisture Volumetric (cm$^3$/cm$^3$)', color='black')
            ax.set_ylim(lower_bound, ymaxplus) # Xlim to below 0 to allow brown colour to show
            for i in range(len(colrange2)):
                ax.fill_between(dtime, lower_bound, sm, where=sm > gradrange[i], facecolor=colrange2[i],
                                alpha=0.2)
            fig.savefig(nld['defaultdir']+"/data/figures/"+uniquefolder+"/SM_year_"+str(year)+".png", dpi=250)
            
           