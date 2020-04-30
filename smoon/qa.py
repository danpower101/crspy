# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 11:22:52 2019

@author: vq18508
"""
from name_list import nld
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

###############################################################################
#                          The flagging                                       #
###############################################################################
def flag_and_remove(df, N0):
    df = df.drop(df[df.MOD > N0].index)   # drop above N0
    df = df.drop(df[df.MOD < (N0*(nld['belowN0']/100))].index) # drop below 0.3 N0
    df = df.reset_index(drop=True)
    
    # Drop >20% diff in timestep
    moddiff=[0]
    for i in range(len(df.MOD)-1):
        later = df['MOD'][i+1]
        earlier = df['MOD'][i]
        currentdiff = (later - earlier)
        moddiff.append(currentdiff)
    df['DIFF'] = moddiff
    
    prcntdiff = [0]
    for i in range(len(df.MOD)-1):
        later = df['DIFF'][i+1]
        earlier = df['MOD'][i]
        indvdiff = (later / earlier)*100
        prcntdiff.append(indvdiff)
    df['PRCNTDIFF'] = prcntdiff
    
    df = df.drop(df[df.PRCNTDIFF > nld['timestepdiff']].index)
    df = df.drop(df[df.PRCNTDIFF < (-nld['timestepdiff'])].index)
    df = df.reset_index(drop=True)
        
    return df

###############################################################################
#                          The plotting                                       #
###############################################################################

def tseriesplots(var, df, defaultdir, country, sitenum):
    """
    Usually the defaultdir/country/sitenum will be assigned in master script.
    
    """
    x = df['DT']
    y = df[var]
    plt.figure(var, figsize =(10,5))
    plt.title(var, fontsize = 16)
    plt.plot(x, y, marker='o', markersize = 0.3,  color='r', linewidth = 0.3)
    plt.savefig(defaultdir+"data/qa/"+country+"_Site_"+sitenum+"/"+var+".png", dpi=250)
    plt.close()


def QA_plotting(df, country, sitenum, defaultdir):
    
    
    df['YEAR'] = df['DT'].dt.year
    df['MONTH'] = df['DT'].dt.month
    df['DAY'] = df['DT'].dt.day
    # Reduce the size to include the variables to be compared - otherwise it's far too big
    dfcomp = pd.DataFrame(df, columns = [ "MOD", "UNMOD", "YEAR", "MONTH", "DAY", "PRESS", "fsol", "fbar", "fawv", "TEMP", 
                                         "BATT", "I_TEMP", "I_RH"])
    
    # Folder Housekeeping - create if not already there
    uniquefolder = country + "_SITE_" + str(sitenum) # Create a folder name for output
    os.chdir(defaultdir + "/data/qa/") # Change wd to folder
    alreadyexist = os.path.exists(uniquefolder) # Checks if the folder exists
    if alreadyexist == False:
        os.mkdir(uniquefolder) # Statement to manage writing a new folder or not depending on existance
    else:
        pass
    os.chdir(defaultdir) # change back
    
    
    # First - correlation heat map    
    plt.figure(101)
    plt.title("Correlation")
    sns.heatmap(dfcomp.corr(), cmap="BuPu") # Heat Map to check for correlations
    plt.savefig(defaultdir+"/data/qa/"+country+"_Site_"+sitenum+"/correlation_heat_map.png")
    plt.close()
    
    #Plot the day/year/month - check for down time
    tseriesplots("YEAR", df, defaultdir, country, sitenum)
    tseriesplots("MONTH", df, defaultdir, country, sitenum)
    tseriesplots("DAY", df, defaultdir, country, sitenum)
    
    #Plot MOD
    tseriesplots("MOD", df, defaultdir, country, sitenum)
    
    # Also add descriptive stats of MOD in a bar chart format below
    desc = df['MOD'].describe()
    desc = desc.drop(desc.index[0]) # Drop Count as its messes with axis
    desc = desc.reset_index()
    plt.figure("DESC", figsize = (10,5))
    plt.title("MOD Descriptive Statistics")
    plt.bar(desc['index'], desc['MOD'], color = "Green")
    plt.savefig(defaultdir+"/data/qa/"+country+"_Site_"+sitenum+"/MOD_descriptive.png", dpi=200)
    plt.close()
    
    # Plot fsol
    tseriesplots("fsol", df,  defaultdir, country, sitenum)
    # Plot fbar
    tseriesplots ("fbar", df, defaultdir, country, sitenum)
    # Plot fawv
    tseriesplots("fawv", df, defaultdir, country, sitenum)
    # Plot PRESS
    tseriesplots("PRESS", df, defaultdir, country, sitenum)
    # Plot TAVG
    tseriesplots("TEMP", df, defaultdir, country, sitenum)
    # Plot PRCP
    tseriesplots("RAIN", df, defaultdir, country, sitenum)
    # Plot VP
    tseriesplots("VP", df, defaultdir, country, sitenum)
    # Plot BATT
    tseriesplots("BATT",df, defaultdir, country, sitenum)
    # Plot I_TEMP
    tseriesplots("I_TEM", df, defaultdir, country, sitenum)
    # Plot I_RH
    tseriesplots("I_RH", df, defaultdir, country, sitenum)
    
    df = df.drop(['YEAR', 'MONTH', 'DAY', 'DIFF', 'PRCNTDIFF'], axis=1)
    df = df.replace(np.nan, nld['noval'])
    return df