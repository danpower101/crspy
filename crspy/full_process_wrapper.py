# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 11:08:09 2020

@author: vq18508

Wrapper function to process the data from start to finish
"""
import re

# crspy funcs
from crspy.tidy_data import prepare_data
from crspy.neutron_coeff_creation import neutcoeffs
from crspy.n0_calibration import n0_calib
from crspy.qa import flag_and_remove
from crspy.qa import QA_plotting
from crspy.theta import thetaprocess
from crspy.gen_funcs import getlistoffiles
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')


def process_raw_data(filepath, calibrate=True, intentype=None, nld=nld):
    """process_raw_data is a function that wraps all the necessary functions to process data. The user can select
    whether to complete n0 calibration (i.e. this may not be required if already done previously). It also gives the option to decide which
    intensity correction method to apply as there are two currently used. If a standard is agreed upon this will adjusted here.

    Parameters
    ----------
    filepath : string
        location of the file to process
        e.g. nld['defaultdir']+"/data/raw/SITE_101"
    calibrate : bool, optional
        state whether the n0 calibration is required, by default True
    N0_2 : integer, optional
        an option to provide a second N0 number to compare new and old processes, by default None
    intentype : string, optional
        user can pass the string "nearestGV" to utilise the method outlined
        by Hawdon et al., (2014) whereby NMDB site with the nearest GV is used, by default None
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars

    Returns
    -------
    df, meta
        the corrected dataframe and metadata are output - they are also saved automatically during running into
        folder structure
    """
    nld=nld['config']
    if calibrate is True:
        
        m = re.search('/crns_data/raw/(.+?).txt', filepath)
        name = m.group(1).lower()
        caliblist = getlistoffiles(nld['defaultdir']+"/data/calibration_data/")
        caliblist = [item.lower() for item in caliblist]
        if any(name in s for s in caliblist):
            print("Calibration data is available, continuing...")
        else:
            print("No calibration data found for selected site, please ensure calibration data is available and labelled correctly or turn off the calibration routine.")
            df=None
            meta=None
            return df,meta

    if intentype == "nearestGV":
        df, country, sitenum, meta, nmdbstation = prepare_data(
            filepath, intentype="nearestGV")
        print("Processing " + str(country)+"_SITE_"+str(sitenum))
        df, meta = neutcoeffs(df, country, sitenum, nmdbstation=nmdbstation)
    else:
        df, country, sitenum, meta = prepare_data(filepath)
        print("Processing " + str(country)+"_SITE_"+str(sitenum))
        df, meta = neutcoeffs(df, country, sitenum)
    if calibrate is True:
        meta, N0 = n0_calib(meta, country, sitenum, float(nld['accuracy']))
    else:
        N0 = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'N0'].item()
    df = flag_and_remove(df, N0, country, sitenum)
    df = QA_plotting(df, country, sitenum, nld['defaultdir'])
    df = thetaprocess(df, meta, country, sitenum)
    return df, meta
