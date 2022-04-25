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


def process_raw_data(filepath, calibrate=True, calib_start_time=None, calib_end_time=None, intentype=None, useera5=True, theta_method="desilets", nld=nld):
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
    calib_start_time : str optional
        start time of calibration period (UTC), if None uses COSMOS-USA deafult time of 16:00:00
        e.g. "15:00:00"
    calib_end_time : str optional
        end time of calibration period (UTC), if None uses COSMOS-USA default time of 23:00:00
        e.g. "22:00:00"
    intentype : string, optional
        user can pass the string "nearestGV" to utilise the method outlined
        by Hawdon et al., (2014) whereby NMDB site with the nearest GV is used, by default None
    useera5 : boolean, optional
        if you wish to not use era5 land data this will entirely skip looking for and using era5-land
        data, default True.
    theta_method: str, optional
        standard method is desilet, added option to use kohli method (see gen funcs - theta_kohli)
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
            filepath, useeradata=useera5, intentype="nearestGV")
        print("Processing " + str(country)+"_SITE_"+str(sitenum))
        df, meta = neutcoeffs(df, country, sitenum, nmdbstation=nmdbstation)
    else:
        df, country, sitenum, meta = prepare_data(filepath, useeradata=useera5)
        print("Processing " + str(country)+"_SITE_"+str(sitenum))
        df, meta = neutcoeffs(df, country, sitenum)

    if calibrate is True:
        if calib_start_time and calib_end_time:
            meta, N0 = n0_calib(meta, country, sitenum, defineaccuracy=float(nld['accuracy']), calib_start_time = calib_start_time, calib_end_time = calib_end_time, theta_method=theta_method)
        else:
            meta, N0 = n0_calib(meta, country, sitenum, defineaccuracy=float(nld['accuracy']), theta_method=theta_method)
    else:
        N0 = meta.loc[(meta.COUNTRY == country) & (
            meta.SITENUM == sitenum), 'N0'].item()

    df = flag_and_remove(df, N0, country, sitenum)
    df = QA_plotting(df, country, sitenum, nld['defaultdir'])
    df = thetaprocess(df, meta, country, sitenum, theta_method=theta_method)
    return df, meta
