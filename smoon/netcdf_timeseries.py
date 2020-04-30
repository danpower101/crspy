# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 13:25:29 2020

@author: Daniel Power

From metadata select sites with appropriate location (e.g. USA, MEX and CAN).
Use this to extract the lat and lon and site code name.


"""

from name_list import nld
import os
os.chdir(nld['defaultdir'])
import xarray as xr
import itertools
import pandas as pd

meta = pd.read_csv(nld['defaultdir']+"/data/meta_data.csv")
meta['SITENUM'] = meta.SITENUM.map("{:03}".format) # Add leading zeros

#add for loop
yearlist= [2014]
months = [7]

# Create placeholder
ds_1 = xr.Dataset()
COSMOS_ERA5_Land_Variables = xr.Dataset()
#take from metadata
for year in yearlist:
    for month in months:
        ncfile = nld['defaultdir']+"/Data/ERA5Land/USA_Continent_"+str(year)+"_month_"+str(month)+"_ERA5Land.nc"
        with xr.open_dataset(ncfile) as ds:
            timearray = list(ds.time.values)   #Extract the times         
            for i in range(len(meta)):
                if (meta.COUNTRY[i] == "USA") or (meta.COUNTRY[i] == "MEX") or (meta.COUNTRY[i] == "CAN"):
                    print(i) 
                    # Assign values of sitename, and location of site.
                    lon = meta.loc[i,"LOC_LON"]
                    lat = meta.loc[i, "LOC_LAT"]
                    sitename = meta['COUNTRY'][i]+"_SITE_"+meta['SITENUM'][i]                    
                    timearray = list(ds.time.values)
                    sitelist = list(itertools.repeat(sitename, len(timearray)))                  
                    
                    # Set index for series - time and site
                    idx = pd.MultiIndex.from_arrays(arrays=[timearray ,sitelist], names=["time","site"])
                    
                    # Create series for each var
                    temp_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').t2m.values, index=idx)
                    press_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').sp.values, index=idx)
                    precip_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').tp.values, index=idx)
                    sm_1_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').swvl1.values, index=idx)
                    sm_2_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').swvl2.values, index=idx)
                    sm_3_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').swvl3.values, index=idx)
                    sm_4_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').swvl4.values, index=idx)
                    dewtemp_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').d2m.values, index=idx)
                    snowequiv_s = pd.Series(ds.sel(latitude=lat, longitude=lon, method='nearest').sd.values, index=idx)
                    
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
                else:
                    pass
                COSMOS_ERA5_Land_Variables = xr.merge([COSMOS_ERA5_Land_Variables, full])
                COSMOS_ERA5_Land_Variables.to_netcdf('COSMOS_ERA5_Land_USA_MEX_CAN.nc') # Save each iteration incase of crash
                