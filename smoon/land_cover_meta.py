import cdsapi
from name_list import nld
import os
os.chdir(nld['defaultdir'])
import xarray as xr
import pandas as pd
import zipfile
import smoon


##############################################

def dl_land_cover():
    """
    Downloads the 2018 global land cover dataset from the cdsapi:
        
    """
    c = cdsapi.Client()
    savezip = nld['defaultdir']+'/data/land_cover_data/land_cover.zip'
    extractzip = nld['defaultdir']+'/data/land_cover_data/'
    
    c.retrieve(
        'satellite-land-cover',
        {
            'variable': 'all',
            'format': 'zip',
            'year': '2018',
            'version': 'v2.1.1',
        },
        nld['defaultdir']+'/data/land_cover_data/land_cover.zip')
    #extract zip
    print("Extracting zip file and deleting zip...")
    with zipfile.ZipFile(savezip, 'r') as zip_ref:
        zip_ref.extractall(extractzip)
    #remove zip for clean folder
    os.remove(nld['defaultdir']+'/data/land_cover_data/land_cover.zip')
    print("Done")
###############################################


def find_lc(lat, lon):
    landdat = smoon.getlistoffiles(nld['defaultdir'] + "/data/land_cover_data/")
    
    #Open file
    tmp = xr.open_dataset(landdat[0])
    
    #Create value dict
    meanings = tmp.lccs_class.flag_meanings
    meanings = pd.Series(meanings.split())
    meannums = pd.Series(tmp.lccs_class.flag_values)
    ludict = dict(zip(meannums,meanings))
    
    #Find value
    tmp2 = tmp.lccs_class.sel(lat=lat, lon=lon, method='nearest').values[0]
    lc = ludict[tmp2]
    return lc