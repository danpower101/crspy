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
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')

def datechange(year, yday):
    """
    Datechange func takes as arguments year and yday and converts it into a
    date. This can then be applied to DAYMET data to give a date that can be
    utilised in a dictionary for combining table values.

    NO LONGER USED
    """
    return datetime.date(int(year), 1, 1) + datetime.timedelta(int(yday) - 1)


def getlistoffiles(dirName):
    """getlistoffiles will create a list of file locations for a given folder. This can then be
    used to ensure all files in a folder are processed.

    Parameters
    ----------
    dirName : string
        string pointing the the directory the user wishes to have a list of files from
        e.g. e.g. "nld['defaultdir']+"/data/rawdata"

    Returns
    -------
    list
        list of files in the directory
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


def flipif(filename, nld=nld):
    """flipif checks to see if time is in ascending or descending order and will convert if needed such
    that:
        time[0] == earliest date
        time[end] == latest date

    Writes out to original file location.

    Parameters
    ----------
    filename : string 
        the filename to check
        e.g. "USA_SITE_011.txt"
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    """
    nld=nld['config']
    m = re.search('/crns_data/raw/(.+?)_',
                  filename)  # (.+?) here is the string being extracted between the series
    if m:
        country = m.group(1)
    else:
        print("Problem with getting the country from file name...")
        return
    m2 = re.search('SITE_(.+?).txt', filename)
    if m2:
        sitenum = m2.group(1)
    else:
        print("Problem with getting the sitenum from file name...")
        return
    tmp = pd.read_csv(nld['defaultdir'] + "/data/crns_data/raw/" +
                      country+"_SITE_" + sitenum+".txt", sep="\t")
    tmp['TIME'] = pd.to_datetime(tmp['TIME']) # need to speed up by defining format (but formats vary). Maybe ifelse..
    if tmp['TIME'].iloc[0] > tmp['TIME'].iloc[-1]:
        tmp = tmp.iloc[::-1]
        tmp.to_csv(nld['defaultdir'] + "/data/crns_data/raw/"+country+"_SITE_" +
                   sitenum+".txt", header=True, index=False, sep="\t",  mode='w')
    else:
        pass


def flipall(listfiles):
    """flipall will take a list of files (see crspy.getlistoffiles) and ensure they are all ascending

    Parameters
    ----------
    listfiles : list
        list of files output by the getlistoffiles func
    """
    for i in range(len(listfiles)):
        print(i)  # Add to see where error occurs if encountered
        filename = listfiles[i]
        try:
            flipif(filename)
        except:
            print("Couldn't complete "+str(filename))

#listfiles = getlistoffiles(nld['defaultdir'] + "/data/crns_data/raw/")
# flipall(listfiles)
