#-*- coding: utf-8 -*-
"""
Created on Mon Jul  6 11:08:09 2020

@author: vq18508

Wrapper function to process the data from start to finish
"""
from name_list import nld

# crspy funcs
from crspy.tidy_data import prepare_data
from crspy.neutron_coeff_creation import neutcoeffs
from crspy.n0_calibration import n0_calib
from crspy.qa import flag_and_remove
from crspy.qa import QA_plotting
from crspy.theta import thetaprocess


def process_raw_data(filepath, calibrate=True, N0_2 = None):
    """
    A function that wraps all the necessary functions to process data. Can select
    whether to do n0 calibration (e.g. may not be required if previously done).
    """
    df, country, sitenum, meta = prepare_data(filepath)
    print("Processing " + str(country)+"_SITE_"+str(sitenum))
    df, meta = neutcoeffs(df, country, sitenum)
    if calibrate is True:
        meta, N0 = n0_calib(meta, country, sitenum, nld['accuracy'])
    else:
        N0 = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'N0'].item()
    df = flag_and_remove(df, N0, country, sitenum)
    df = QA_plotting(df, country, sitenum, nld['defaultdir'])
    if N0_2 != None:
        df = thetaprocess(df, meta, country, sitenum, N0_2=N0_2)
    else:
        df = thetaprocess(df, meta, country, sitenum)
    return df, meta