# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 08:43:31 2020

@author: Daniel Power 

Function to download ERA5_Land data from (https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=form)
inside python. 

Requires setting up computer as outlined in readme.md due to a requirement to register and log in to system.

Set up like this as it can take a LONG time to download. Best to leave running over a few days depending on amount being downloaded.
"""
from name_list import nld
import os
os.chdir(nld['defaultdir'])
import cdsapi
import xarray as xr
import itertools
import pandas as pd


def era5landdl(area, years, months, variables, savename):
    """
    Function to automate download of ERA5_Land data. See readme for instructions
    on preparing the computer log in to era5 land system, necessary to run this code.
    
    Parameters:
        area = list of max degrees in each direction in the form [north,west,south,east] 
                e.g. [72,-156.7, 29.7, -68]
                
        years = list of years to download
                e.g. [2015,2016,2017] 
                
        months = list of months to download (numeric)
                e.g. [1,2,3,4,5,6,7,8,9,10,11,12]
                
        variables = list of variable names (see ERA5_Land documentation for full list available)
                e.g. [
                        '2m_temperature', 'surface_pressure', 'total_precipitation',
                        'volumetric_soil_water_layer_1', 'volumetric_soil_water_layer_2', 'volumetric_soil_water_layer_3',
                        'volumetric_soil_water_layer_4','2m_dewpoint_temperature','snow_depth_water_equivalent'
                        ]
                
        savename = string to identify the area being downloaded
                e.g. "USA_Sites"
        
    """
    for year in years:
        for month in months:
            slocation = nld['defaultdir']+"/data/era5land/store/"+savename+"_"+str(year)+"_month"+str(month)+".nc"
            c = cdsapi.Client()
            c.retrieve(
                'reanalysis-era5-land',
                {
                    'variable': variables,
                    'year': year,
                    'month': month, # change month to monthlist if yearly
                    'day': [
                        '01', '02', '03',
                        '04', '05', '06',
                        '07', '08', '09',
                        '10', '11', '12',
                        '13', '14', '15',
                        '16', '17', '18',
                        '19', '20', '21',
                        '22', '23', '24',
                        '25', '26', '27',
                        '28', '29', '30',
                        '31',
                    ],
                    'area': area,
                    'time': [
                        '00:00', '01:00', '02:00',
                        '03:00', '04:00', '05:00',
                        '06:00', '07:00', '08:00',
                        '09:00', '10:00', '11:00',   # All times
                        '12:00', '13:00', '14:00',
                        '15:00', '16:00', '17:00',
                        '18:00', '19:00', '20:00',
                        '21:00', '22:00', '23:00',
                    ],
                    'format': 'netcdf'
                },
                 
                slocation)
            
    
def era5landnetcdf(years, months, tol, loadname, savename, ogfile=None):
    """
    Takes individual era5land files from websiteand extracts the required grids.
    It then combines them into a single netcdf file with dimensions date and site.
    
    It will identify the correct grid using the nearest lat and lon within a defined
    tolerance, to ensure grids aren't taken from too far away from site.
    
    Parameters:
        years = list of years which should match data that has been downloaded
        
        months = list of months which should match data that has been downloaded
        
        tol = tolerance (degrees) on finding nearest grid to site location
            e.g. 0.1 is recommended as this is the resolution of ERA5_Land data
        
        loadname = string for the name used in the era5landdl function (savename)
            e.g. 
        
        savename = string for the output filename wanted
            e.g. "COSMOS_ERA5_data"
        
        ogfile = string location of the original netcdf file (if available). If not 
                available it will make a new one, if it is available it will concat
                data to this file. 
                If none available string should be "None"
            e.g. nld['defaultdir']+"/data/era5_land/era5land_all_sites.nc" or "None"
    
    """
    meta = pd.read_csv(nld['defaultdir']+"/data/metadata.csv")
    meta['SITENUM'] = meta.SITENUM.map("{:03}".format) # Add leading zeros
    
    
    # Create placeholder
    ds_1 = xr.Dataset()
    if ogfile == "None":
        era5_all = xr.Dataset()
    else:
        era5_all = xr.open_dataset(ogfile)
    
    #take from metadata
    for year in years:
        for month in months:
            ncfile = nld['defaultdir']+"/data/era5land/store/"+loadname+"_"+str(year)+"_month"+str(month)+".nc"
            print("Extracting data from "+ncfile)
            with xr.open_dataset(ncfile) as ds:
                timearray = list(ds.time.values)   #Extract the times
                
                """
                Trial and error method. Go through the metadata, extract lat lon,
                extract site name and code, then attempt to find the data within the 
                defined tolerance from the data in the store folder.
                If not found will move onto the next.
                """
                
                for i in range(len(meta)):
                    # Assign values of sitename, and location of site.
                    lon = meta.loc[i,"LONGITUDE"]
                    lat = meta.loc[i, "LATITUDE"]
                    sitename = meta['COUNTRY'][i]+"_SITE_"+meta['SITENUM'][i]                    
                    timearray = list(ds.time.values)
                    sitelist = list(itertools.repeat(sitename, len(timearray)))                  
                    
                    # Set index for series - time and site
                    idx = pd.MultiIndex.from_arrays(arrays=[timearray ,sitelist], names=["time","site"])
                    
                    # Create series for each var
                    try:
                        temp_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).t2m.values, index=idx)
                        press_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).sp.values, index=idx)
                        precip_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).tp.values, index=idx)
                        sm_1_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).swvl1.values, index=idx)
                        sm_2_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).swvl2.values, index=idx)
                        sm_3_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).swvl3.values, index=idx)
                        sm_4_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).swvl4.values, index=idx)
                        dewtemp_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).d2m.values, index=idx)
                        snowequiv_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest', tolerance = tol).sd.values, index=idx)
                     
                        # Create dataarray for each var
                        temp_da = xr.DataArray.from_series(temp_s)
                        press_da = xr.DataArray.from_series(press_s)
                        precip_da = xr.DataArray.from_series(precip_s)
                        sm_1_da = xr.DataArray.from_series(sm_1_s)
                        sm_2_da = xr.DataArray.from_series(sm_2_s)
                        sm_3_da = xr.DataArray.from_series(sm_3_s)
                        sm_4_da = xr.DataArray.from_series(sm_4_s)
                        dewtemp_da = xr.DataArray.from_series(dewtemp_s)
                        snowequiv_da = xr.DataArray.from_series(snowequiv_s)
                                            
                        dstemp = xr.Dataset(data_vars={"temperature":temp_da,
                                                   "pressure":press_da,                                                  
                                                   "precipitation":precip_da,
                                                   "soil_moisture_1": sm_1_da,
                                                   "soil_moisture_2": sm_2_da,
                                                   "soil_moisture_3": sm_3_da,
                                                   "soil_moisture_4": sm_4_da,
                                                   "dewpoint_temperature": dewtemp_da,
                                                   "snow_water_equiv": snowequiv_da})
                        
                        ds_1 = ds_1.combine_first(dstemp)
                        print("Writing "+sitename)
                    except:
                        pass
                era5_all = xr.merge([era5_all, ds_1])
                era5_all.to_netcdf(nld['defaultdir']+"/data/era5land/"+savename+'.nc') # Save each iteration incase of crash!
