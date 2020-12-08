"""
Generic Functions

author: Daniel Power - University of Bristol PhD student

email: daniel.power@bristol.ac.uk

##############################################################################
A collection of functions used in the processing of the data   
##############################################################################

"""
import datetime
import os
import re
import pandas as pd
from name_list import nld

def datechange (year, yday):
    """datechange func takes as arguments year and yday and converts it into a
    date. This can then be applied to DAYMET data to give a date that can be
    utilised in a dictionary for combining table values."""
    return datetime.date(int(year), 1, 1) + datetime.timedelta(int(yday) - 1)

def getlistoffiles(dirName):
    """
    Will create a list of file locations for a given folder. This can then be
    used to ensure all files in a folder are processed. 
    """
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getlistoffiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles

def flipif(filename):
    """
    Feed in filename as a string that contains hydroinnova data. Checks to see
    if time is earliest first or latest first and will convert if needed such
    that:
        time[0] == earliest date
        time[end] == latest date
    
    Writes out to original file location.
    """
    m = re.search('/crns_data/raw/(.+?)_', filename) #  (.+?) here is the string being extracted between the series
    if m:
        country = m.group(1)
    m2 = re.search('SITE_(.+?).txt',filename)
    if m2:
        sitenum = m2.group(1)
      
    tmp = pd.read_csv(nld['defaultdir'] + "/data/crns_data/raw/"+country+"_SITE_" + sitenum+".txt", sep="\t")
    
    if tmp['TIME'].iloc[0] > tmp['TIME'].iloc[-1]:
        tmp = tmp.iloc[::-1]
        tmp = tmp[~tmp.TIME.str.contains("2009")] # remove data from 2009
        tmp.to_csv(nld['defaultdir'] + "/data/crns_data/raw/"+country+"_SITE_" + sitenum+".txt", header=True, index=False, sep="\t",  mode='w')
    else:
        pass

def flipall(listfiles):
    """
    Iterate flipping function through the list of files
    """
    for i in range(len(listfiles)):
        print(i) # Add to see where error occurs if encountered
        filename = listfiles[i]
        flipif(filename)

#listfiles = getlistoffiles(nld['defaultdir'] + "/data/crns_data/raw/")
#flipall(listfiles)  
