"""
Created on Wed Aug 28 15:20:35 2019

@author: Daniel Power
Email: daniel.power@bristol.ac.uk

This module takes in the combined data from combine_data.py and processes the 
neutron correction. It creates a column with the relevant coefficients. This 
allows detailed look at how each coefficient impacts theta.

Citations: 
    Hawdon, A., D. McJannet, and J. Wallace (2014), 
    Calibration and correction procedures for cosmic-ray neutron soil moisture 
    probes located across Australia, 
    Water Resour. Res., 50, 5029–5043, doi:10.1002/ 2013WR015138.

    Rosolem, R. and Shuttleworth, W. J. and Zreda, M. and Franz, T. E. and 
    Zeng, X. and Kurc, S. A. (2013),
    The effect of atmospheric water vapor on neutron count in the cosmic-ray soil 
    moisture observing system,
    Journal of Hydrometeorology, 14, 1659--1671
    
    Baatz, R., H. R. Bogena, H.-J. Hendricks Franssen, J. A. Huisman, C. Montzka, 
    and H. Vereecken (2015), 
    An empirical vegetation correction for soil water content quantification using 
    cosmic ray probes, Water Resour. Res., 51, 2030–2046, doi:10.1002/ 2014WR016443.
    
"""
import math
import pandas as pd  # Pandas for dataframe
import numpy as np

# crspy funcs
from crspy.neutron_correction_funcs import (
    pv,
    humfact,
    pressfact_B,
    finten,
    RcCorr,
    agb,
)
from crspy.additional_metadata import nmdb_get
"""
To stop import issue with the config file when importing crspy in a wd without a config.ini file in it we need
to read in the config file below and add `nld=nld['config']` into each function that requires the nld variables.
"""
from configparser import RawConfigParser
nld = RawConfigParser()
nld.read('config.ini')


def neutcoeffs(df, country, sitenum, nmdbstation=None, nld=nld):
    """neutcoeffs provides the factors to multiply the neutron count by to account for external impacts

    Parameters
    ----------
    df : dataframe
        dataframe of the tidied site data
    country : str
        country e.g. "USA"
    sitenum : str
        sitenume e.g. "011"
    nmdbstation : str, optional
        if not JUNG then here goes the nmdb station code, by default None
    nld : dictionary
        nld should be defined in the main script (from name_list import nld), this will be the name_list.py dictionary. 
        This will store variables such as the wd and other global vars


    Returns
    -------
    dataframe
        returns the dataframe with values for neutron correction appended
    """
    nld=nld['config']
    print("~~~~~~~~~~~~~ Calculate Neutron Correction Factors ~~~~~~~~~~~~~")
    # Read in meta fresh
    meta = pd.read_csv(nld['defaultdir']+"/data/metadata.csv")
    meta['SITENUM'] = meta.SITENUM.map(
        "{:03}".format)  # Ensure its three digits

    df = df.replace(int(nld['noval']), np.nan)

    ###############################################################################
    #                    Atmospheric Water Vapour                                 #
    ###############################################################################
    """
    Rosolem et al., (2013)
    
    Uses ERA5_Land data for vapour pressure and temperature to find absolute humidity.
    This can then be converte to neutrons which is again converted to a coefficient
    for tidy data. Ref pressure of PV0 is always set to 0.
    """
    # Define Constant

    # VP is in Pascals and TEMP is in Cel
    df['pv'] = df.apply(lambda row: pv(row['VP'], row['TEMP']), axis=1)
    df['pv'] = df['pv']*1000  # convert Kg m-3 to g m-3
    df["fawv"] = df.apply(lambda row: humfact(row['pv'], float(nld['pv0'])), axis=1)

    ###############################################################################
    #                            Pressure                                         #
    ###############################################################################

    """
    
    """
    refpres = meta.loc[(meta.SITENUM == sitenum) & (
        meta.COUNTRY == country), "REFERENCE_PRESS"].item()
    beta = meta.loc[(meta.SITENUM == sitenum) & (
        meta.COUNTRY == country), "BETA_COEFF"].item()
    df['fbar'] = df.apply(lambda row: pressfact_B(
        row['PRESS'], beta, refpres), axis=1)

    ###############################################################################
    #                       Solar Intensity                                       #
    ###############################################################################
    """
    The fsol comes from HydroInnova - update required to correct the coefficient for
    the differencee in cutoff ridgitiy (GV) between Junfraujoch and the CRNS site.
    
    See Hawdon et al (2014) for full explanation - equation taken from that paper.
    """
    if nmdbstation != None:
        tmp = nmdb_get("2011-05-01", "2011-05-01", str(nmdbstation))
        dt = next(iter(tmp))
        x = tmp[dt]
        x = float(x)  # get value
        df['finten'] = df.apply(
            lambda row: finten(x, row['NMDB_COUNT']), axis=1)

    else:
        Rc = meta.loc[(meta.SITENUM == sitenum) & (
            meta.COUNTRY == country), "GV"].item()
        RcCorrval = RcCorr(Rc)
        df['finten_noGV'] = df.apply(lambda row: finten(
            int(nld['jung_ref']), row['NMDB_COUNT']), axis=1)

        df['finten'] = (df['finten_noGV'] - 1) * RcCorrval + 1

    ###############################################################################
    #                       Above Ground Biomass                                  #
    ###############################################################################
    """
    The agbval comes from metadata and is above ground biomas (Kg m^2). Currently
    using a single value but hope in the future to find seasonal data.   
    """
    # The below bwe will eventually be read in from metadata file or a bwe file
    # Taken from supplemental data of Franz et al., 2012
    agbval = meta.loc[(meta.COUNTRY == country) & (
        meta.SITENUM == sitenum), 'AGBWEIGHT'].item()
    if math.isnan(agbval):  # Introduce catch incase info isn't available
        df['fagb'] = 1
    else:
        df['fagb'] = df.apply(lambda row: agb(agbval), axis=1)

    ###############################################################################
    #                        Corrected Neutrons                                   #
    ###############################################################################
    """
    Need to create the MODCORR which is corrected neutrons. 
    """
    df['MOD_CORR'] = df['MOD'] * df['fbar'] * \
        df['finten'] * df['fawv'] * df['fagb']
    df['MOD_CORR'] = df['MOD_CORR'].apply(np.floor)

    # Error is the ((standard deviation) / MOD)*MODCORR
    df['MOD_ERR'] = (np.sqrt(df['MOD'])/df['MOD']) * df['MOD_CORR']
    df['MOD_ERR'] = df['MOD_ERR'].apply(np.floor)

    # Remove calcs done on missing data
    DTstore = df['DT']
    df = df.reset_index(drop=True)
    df.loc[df['finten'].isnull(), :] = np.nan
    df = df.set_index(DTstore)
    df['DT'] = df.index
    df = df.replace(np.nan, int(nld['noval']))
    df = df.round(3)  # decimal place limit

    # Save Lvl1 data
    df.to_csv(nld['defaultdir'] + "/data/crns_data/level1/"+country+"_SITE_" + sitenum+"_LVL1.txt",
              header=True, index=False, sep="\t",  mode='w')
    meta.to_csv(nld['defaultdir'] + "/data/metadata.csv",
                header=True, index=False, mode='w')
    print("Done")
    return df, meta
