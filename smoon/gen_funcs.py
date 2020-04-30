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
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles