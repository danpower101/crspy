# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 11:22:52 2019

@author: vq18508
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')

###############################################################################
#                          The flagging                                       #
###############################################################################
def flag_and_remove(df, N0, country, sitenum, nld=nld):
    """flag_and_remove identifies data that should be flagged based on the following criteria and removes it:
    Flags:
        1 = fast neutron counts more than 20% difference to previous count
        2 = fast neutron counts less than the minimum count rate (default == 30%, can be set in namelist)
        3 = fast neutron counts more than n0
        4 = battery below 10v


    Parameters
    ----------
    df : dataframe
        dataframe of the CRNS data
    N0 : int
        N0 number
    country : str
        string of country e.g. "USA"
    sitenum : str
        string o sitenum e.g. "011"
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']
    print("~~~~~~~~~~~~~ Flagging and Removing ~~~~~~~~~~~~~")
    print("Identifying erroneous data...")
    idx = df['DT']
    idx = pd.to_datetime(idx)

    # Need to save external variables as when deleting and reindexing they are lost

    tmptemp = df['TEMP']
    tmprain = df['RAIN']
    tmpvp = df['VP']
    tmpdp = df['DEWPOINT_TEMP']
    tmpswe = df['SWE']

    # Reset index incase df is from another process and is DT
    df = df.reset_index(drop=True)
    df2 = df.copy()
    df2['FLAG'] = 0  # initialise FLAG to 0

    # Flag consistent with COSMOS-USA system
    df2.loc[df2.MOD_CORR > N0, "FLAG"] = 3
    df = df.drop(df[df.MOD_CORR > N0].index)   # drop above N0

    df2.loc[(df2.MOD_CORR < (N0*(int(nld['belowN0'])/100))) &
            (df2.MOD_CORR != int(nld['noval'])), "FLAG"] = 2
    # drop below 0.3 N0
    df = df.drop(df[df.MOD_CORR < (N0*(int(nld['belowN0'])/100))].index)
   # df = df.reset_index(drop=True)

    df2.loc[(df2.BATT < 10) & (df2.BATT != int(nld['noval'])), "FLAG"] = 4
    df = df.drop(df[df.BATT < 10].index)

   # df = df.reset_index(drop=True)
    # Drop >20% diff in timestep

    moddiff = [0]
    tmpindex = list(df.index)
    for i in range(len(tmpindex)-1):
        lateridx = tmpindex[i+1]
        earlieridx = tmpindex[i]
        later = df['MOD'][lateridx]
        earlier = df['MOD'][earlieridx]
        currentdiff = (later - earlier)
        moddiff.append(currentdiff)
    df['DIFF'] = moddiff

    prcntdiff = [0]
    for i in range(len(tmpindex)-1):
        lateridx = tmpindex[i+1]
        earlieridx = tmpindex[i]
        later = df['DIFF'][lateridx]
        earlier = df['MOD'][earlieridx]
        indvdiff = (later / earlier)*100
        prcntdiff.append(indvdiff)
    df['PRCNTDIFF'] = prcntdiff

    df['INDEX_TMP'] = df.index

    diff1 = df.loc[(df['PRCNTDIFF'] > int(nld['timestepdiff'])), "INDEX_TMP"]
    #diff1 = diff1[0]
    diff2 = df.loc[(df['PRCNTDIFF'] < (-int(nld['timestepdiff']))), "INDEX_TMP"]
    #diff2 = diff2[0]

    df2 = df2.reset_index(drop=True)
    df2.loc[diff1, "FLAG"] = 1
    df2.loc[diff2, "FLAG"] = 1

    df = df.drop(df[df.PRCNTDIFF > int(nld['timestepdiff'])].index)
    df = df.drop(df[df.PRCNTDIFF < (-int(nld['timestepdiff']))].index)
    #df = df.reset_index(drop=True)

    # Fill in master time again after removing
    # Need this to handle below code
    df.replace(int(nld['noval']), np.nan, inplace=True)
    df['DT'] = pd.to_datetime(df['DT'], format="%Y-%m-%d %H:%M:%S")
    df = df.set_index(df.DT)
    df = df.reindex(idx, fill_value=np.nan)
    df['DT'] = pd.to_datetime(df['DT'])

    flagseries = df2['FLAG']
    df['FLAG'] = flagseries.values  # Place flag vals back into df
    df['DT'] = df.index

    df = df.drop(["DIFF", "PRCNTDIFF", "INDEX_TMP"], axis=1)

    insertat = len(df.columns)-3
    dtcol = df['FLAG']
    df.drop(labels=['FLAG'], axis=1, inplace=True)  # Move FLAG to first col
    df.insert(insertat, 'FLAG', dtcol)

    # Add the external variables back in

    df['TEMP'] = tmptemp
    df['RAIN'] = tmprain
    df['VP'] = tmpvp
    df['DEWPOINT_TEMP'] = tmpdp
    df['SWE'] = tmpswe

    df = df.replace(np.nan, int(nld['noval']))

    df.to_csv(nld['defaultdir'] + "/data/crns_data/FINAL/"+country+"_SITE_" + sitenum+"_final.txt",
              header=True, index=False, sep="\t", mode='w')
    print("Done")
    return df

###############################################################################
#                          The plotting                                       #
###############################################################################


def tseriesplots(var, df, defaultdir, country, sitenum):
    """tseriesplots creates time series plots of variables in df for visual checks

    Parameters
    ----------
    var : str
        variable to plot
    df : dataframe
        dataframe of the CRNS site
    defaultdir : str
        working directory
    country : str
        country e.g. "USA"
    sitenum : str
        sitenum e.g. "011"
    
    """
    x = df['DT']
    y = df[var]
    plt.figure(var, figsize=(10, 5))
    plt.title(var, fontsize=16)
    plt.plot(x, y, marker='o', markersize=0.3,  color='r', linewidth=0.3)
    plt.savefig(defaultdir+"/data/qa/"+country +
                "_Site_"+sitenum+"/"+var+".png", dpi=250)
    plt.close()


def QA_plotting(df, country, sitenum, defaultdir, nld=nld):
    """QA_plotting function to output QA plots

    Parameters
    ----------
    df : dataframe
        CRNS site dataframe
    country : str
        country e.g. "USA"
    sitenum : str
        sitenum e.g. "011"
    defaultdir : str
        working directory
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']
    print("~~~~~~~~~~~~~ Plotting QA Graphs ~~~~~~~~~~~~~")
    print("Saving plots...")
    # set error to nan values for plotting
    df = df.replace(int(nld['noval']), np.nan)
    df['YEAR'] = df['DT'].dt.year
    df['MONTH'] = df['DT'].dt.month
    df['DAY'] = df['DT'].dt.day
    # Reduce the size to include the variables to be compared - otherwise it's far too big
    dfcomp = pd.DataFrame(df, columns=["MOD", "UNMOD", "YEAR", "MONTH", "DAY", "PRESS", "finten", "fbar", "fawv", "TEMP",  # !!!
                                       "BATT", "I_TEMP", "I_RH"])

    # Folder Housekeeping - create if not already there
    # Create a folder name for output
    uniquefolder = country + "_SITE_" + str(sitenum)
    os.chdir(defaultdir + "/data/qa/")  # Change wd to folder
    alreadyexist = os.path.exists(uniquefolder)  # Checks if the folder exists
    if alreadyexist == False:
        # Statement to manage writing a new folder or not depending on existance
        os.mkdir(uniquefolder)
    else:
        pass
    os.chdir(defaultdir)  # change back

    # First - correlation heat map
    plt.figure(101)
    plt.title("Correlation")
    # Heat Map to check for correlations
    sns.heatmap(dfcomp.corr(), cmap="BuPu")
    plt.savefig(defaultdir+"/data/qa/"+country+"_Site_" +
                sitenum+"/correlation_heat_map.png")
    plt.close()

    # Plot the day/year/month - check for down time
    tseriesplots("YEAR", df, defaultdir, country, sitenum)
    tseriesplots("MONTH", df, defaultdir, country, sitenum)
    tseriesplots("DAY", df, defaultdir, country, sitenum)

    # Plot MOD
    tseriesplots("MOD", df, defaultdir, country, sitenum)

    # Also add descriptive stats of MOD in a bar chart format below
    desc = df['MOD'].describe()
    desc = desc.drop(desc.index[0])  # Drop Count as its messes with axis
    desc = desc.reset_index()
    plt.figure("DESC", figsize=(10, 5))
    plt.title("MOD Descriptive Statistics")
    plt.bar(desc['index'], desc['MOD'], color="Green")
    plt.savefig(defaultdir+"/data/qa/"+country+"_Site_" +
                sitenum+"/MOD_descriptive.png", dpi=200)
    plt.close()

    # Plot fsol
    tseriesplots("finten", df,  defaultdir, country, sitenum)
    # Plot fbar
    tseriesplots("fbar", df, defaultdir, country, sitenum)
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
    tseriesplots("BATT", df, defaultdir, country, sitenum)
    # Plot I_TEMP - add try catch as MAY not have this data (above data needs to be available)
    try:
        tseriesplots("I_TEM", df, defaultdir, country, sitenum)
    except:
        print("No I_TEM data")
    # Plot I_RH
    try:
        tseriesplots("I_RH", df, defaultdir, country, sitenum)
    except:
        print("No I_RH data")
    df = df.drop(['YEAR', 'MONTH', 'DAY'], axis=1)
    df = df.replace(np.nan, int(nld['noval']))
    print("Done")
    return df
