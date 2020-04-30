# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 11:28:29 2020

@author: Daniel Power

Here are the places to change the variables to the relevant files on your computer
"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                            # Working Directory Location
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
defaultdir = "C:/user/example_working_directory" # CHANGE THIS TO YOUR WORKING DIRECTORY

noval = -999

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                                # Pressure values
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
"""
Used in the calculation of pressure corrections:
pv0 = reference pressure (hPa)
"""
pv0=0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                                # N0 calibration
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
"""
These parameters are used in N0 calibration.
defaultbd = the value of bulk density (g/cm^3) to use when none available (default is 1.43)
cdtformat = the date format found in calibration data - default is based on COSMOS-USA format
accuracy = the accuracy desired
"""
defaultbd = 1.43
cdtformat = "%d/%m/%Y"
accuracy = 0.01

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                                        # QA
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
"""
Flagging and quality analysis

belowN0 = the bottom limit of neutron counts. Default is 30, meaning counts below
          30% of N0 are removed
timestepdiff = the maximum change between time steps as a percent. 20% is the 
                recommended value.
"""
belowN0 = 30
timestepdiff = 20

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                                        # Theta
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
"""
The a0,a1,a2 coeffs are here but should not be changed unless testing theory of 
converting neutron counts to soil moisture

density = density of material in ground (default set to 2.65 g/cm^3 which is quartz)
"""
density = 2.65

"""
Daily soil moisture data is noisy and so a smoothing function is employed. Select
the window (number of hours) and the type (mean, or SG filter).

smwindow = [6+] number of hours to utlise in filter (default is 12)
smfilter = [SG, mean] SG is Savitsky Golay. Mean uses previous x values to give mean
"""
smwindow = 12
smfilter = "SG"








#Should NOT change
a0 = 0.0808; a1 = 0.372; a2 = 0.115



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
                                # Dictionary Creation
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
nld = {
       "defaultdir":defaultdir,
       "smwindow":smwindow,
       "smfilter":smfilter,
       "a0":a0,
       "a1":a1,
       "a2":a2,
       "defaultbd":defaultbd,
       "cdtformat":cdtformat,
       "daymeted": daymeted,
       "accuracy":accuracy,
       "belowN0":belowN0,
       "timestepdiff":timestepdiff,
       "density":density,
       "edy":edy,
       "noval":noval,
       "pv0":pv0
       }
