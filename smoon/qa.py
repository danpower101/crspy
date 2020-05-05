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


df = pd.read_csv(nld['defaultdir']+"data/crns_data/level1/USA_SITE_011_LVL1.txt", sep="\t")
###############################################################################
#                          The flagging                                       #
###############################################################################
def flag_and_remove(df, N0):
    """
    Quality control to remove values that are in error. 
    
    Flags:
        1 = fast neutron counts more than 20% difference to previous count
        2 = fast neutron counts less than the minimum count rate (default == 30%, can be set in namelist)
        3 = fast neutron counts more than n0
        4 = battery below 10v
        5 = no count for MOD
        
    """
    print("~~~~~~~~~~~~~ Flagging and Removing ~~~~~~~~~~~~~")
    print("Identifying erroneous data...")
    idx = df['DT']
    idx = pd.to_datetime(idx)
    #idx = pd.date_range(idx[0], idx[-1], freq='1H', closed='left')

    df2 = df.copy()
    df2['FLAG'] = 0 # initialise FLAG to 0
    
    df2.loc[df2.MOD > N0, "FLAG"] = 3 # Flag consistent with COSMOS-USA system
    df = df.drop(df[df.MOD > N0].index)   # drop above N0
    
    df2.loc[(df2.MOD < (N0*(nld['belowN0']/100))) & (df2.MOD != nld['noval']), "FLAG"] = 2
    df = df.drop(df[df.MOD < (N0*(nld['belowN0']/100))].index) # drop below 0.3 N0
    df = df.reset_index(drop=True)
    
    df2.loc[(df2.BATT < 10) & (df2.BATT != nld['noval']), "FLAG"] = 4
    df = df.drop(df[df.BATT < 10].index)
    
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
    
    diff1 = np.where(df['PRCNTDIFF'] > nld['timestepdiff'])
    diff1 = diff1[0]
    diff2 = np.where(df.PRCNTDIFF < (-nld['timestepdiff']))
    diff2 = diff2[0]
    
    df2.loc[diff1, "FLAG"] = 1
    df2.loc[diff2, "FLAG"] = 1    

    
    df = df.drop(df[df.PRCNTDIFF > nld['timestepdiff']].index)
    df = df.drop(df[df.PRCNTDIFF < (-nld['timestepdiff'])].index)
    #df = df.reset_index(drop=True)
    
    # Fill in master time again after removing
    df.replace(-999, np.nan, inplace=True) # Need this to handle below code
    df['DT'] = pd.to_datetime(df['DT'], format="%Y-%m-%d %H:%M:%S")
    df = df.set_index(df.DT)
    df = df.reindex(idx, fill_value=nld['noval'])
    df['DT'] = pd.to_datetime(df['DT'])
    df.loc[df.MOD == nld['noval'], :] = nld['noval']
    flagseries = df2['FLAG']
    df['FLAG'] = flagseries.values # Place flag vals back into df
    df['DT'] = df.index
    
    df=df.drop(["DIFF","PRCNTDIFF"], axis =1)
    
    df.to_csv(nld['defaultdir'] + "/data/crns_data/level1/"+country+"_SITE_" + sitenum+"_LVL1.txt",
          header=True, index=False, sep="\t", mode='w')
    print("Done")
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
    
    print("~~~~~~~~~~~~~ Plotting QA Graphs ~~~~~~~~~~~~~")
    print("Saving plots...")
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
    
    df = df.drop(['YEAR', 'MONTH', 'DAY', 'DIFF', 'PRCNTDIFF', "CALIBCORR"], axis=1)
    df = df.replace(np.nan, nld['noval'])
    print("Done")
    return df