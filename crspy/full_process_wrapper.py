#-*- coding: utf-8 -*-
"""
Created on Mon Jul  6 11:08:09 2020

@author: vq18508

Wrapper function to process the data from start to finish
"""
from name_list import nld
import crspy

def process_raw_data(filepath, calibrate=True, N0_2 = None):
    """
    A function that wraps all the necessary functions to process data. Can select
    whether to do n0 calibration (e.g. may not be required if previously done).
    """
    df, country, sitenum, meta = crspy.prepare_data(filepath)
    print("Processing " + str(country)+"_SITE_"+str(sitenum))
    df, meta = crspy.neutcoeffs(df, country, sitenum)
    if calibrate is True:
        meta, N0 = crspy.n0_calib(meta, country, sitenum, nld['accuracy'])
    else:
        N0 = meta.loc[(meta.COUNTRY == country) & (meta.SITENUM == sitenum), 'N0'].item()
    df = crspy.flag_and_remove(df, N0, country, sitenum)
    df = crspy.QA_plotting(df, country, sitenum, nld['defaultdir'])
    if N0_2 != None:
        df = crspy.thetaprocess(df, meta, country, sitenum, N0_2=N0_2)
    else:
        df = crspy.thetaprocess(df, meta, country, sitenum)
    return df, meta