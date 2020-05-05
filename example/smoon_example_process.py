# -*- coding: utf-8 -*-
"""
Processing Cosmic Ray Neutron Sensor (CRNS) Data.

This package will allow complete processing of CRNS data. Here the example has
been provided using HydroInnova data.

Initialisation steps should be followed as described in the README file.


"""

# Before we begin
"""
Scripts should start by importing the name_list file, here as nld. This allows
universal changes to be easily implemented. Next the smoon library should be
imported as well as matplotlib.pyplot for plotting further down. 
"""
from name_list import nld
import smoon
import matplotlib.pyplot as plt

################################ Find Files ###################################
"""
This generic function will list all the files in a directory. Keep raw data in
the raw folder and run as below to give a list of all files. This makes selection
much easier. A loop could be written or select using file_path like below.
"""
file_list = smoon.getlistoffiles(nld['defaultdir'] + "/data/crns_data/raw/")
file_path = file_list[0]

############################### Tidy Up #######################################
"""
tidyup function takes file_path and provides the "tidy" dataframe, country, sitenum
and meta data file. The df will be adjusted to give uniform hourly readings. It
will calculate the site beta coefficient for use in pressure corrections. It will
also check for local variable availability. If required variables are not available in
raw data it will use era5_land data (see era5_land example). 
 
"""

df, country, sitenum, meta = smoon.tidyup(file_path)

############################# Neutron Coefficients ############################
"""
Takes tidy data, creates neutron correction factors for pressure, humidity, 
solar intensity and aboveground biomass. Saves the dataframe and outputs df and metadata. 
"""
# Output the new df plus updated meta

df, meta = smoon.neutcoeffs(df, country, sitenum)

############################ N0 Calibration ################################
"""
N0 calibration script. Output is the meta_data with the updated N0 value and N0.

The inputs are the meta data file, country and sitenum to identify the site of interest,
the accuracy to aim for and a boolean for whether to overwrite the metadata csv file with
the new n0. This is to allow testing of N0 without changing the csv file.
"""

meta, N0 = smoon.n0_calib(meta, country, sitenum, nld['accuracy'], write=True)

###############################################################################
#                          Quality Analysis                                   #
###############################################################################
"""



"""

# flag and remove the datapoints that get flagged
df = smoon.flag_and_remove(df, N0)

df = smoon.QA_plotting(df, country, sitenum, nld['defaultdir'])


###############################################################################
#                          Theta Calculation                                  #
###############################################################################

tmp2, tmpclean2 = smoon.thetaprocess(df, meta, country, sitenum)

tmp2.to_csv(nld['defaultdir'] + "/data/crns_data/theta/"+country+"_SITE_"+sitenum+"_SM.txt",
                 header=True, index=False, sep="\t", mode="w")

plt.plot(tmpclean2['SM_12h_SG'])
