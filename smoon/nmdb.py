# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 11:20:42 2020

@author: vq18508
"""
from name_list import nld
import urllib
import pandas as pd
from bs4 import BeautifulSoup

startdate = "2015-10-01"
enddate = "2016-10-01"
def nmdb_get(startdate, enddate):
    """
    Will collect data for Junfraujoch station that is required to calculate fsol.
    Returns a dictionary that can be used to fill in values to the main dataframe
    of each site.
    
    Parameters:
        startdate = date of the format YYYY-mm-dd
            e.g 2015-10-01
        enddate = date of the format YYYY-mm-dd
            e.g. 2016-10-01
    """
    #split for use in url
    sy,sm,sd = str(startdate).split("-")
    ey,em,ed = str(enddate).split("-")
    
    #Collect html from request and extract table and write to dict
  #!!!WRONG  url = "http://nest.nmdb.eu/draw_graph.php?formchk=1&stations[]=JUNG&tabchoice=1h&dtype=corr_for_efficiency&tresolution=0&yunits=0&date_choice=bydate&start_day={sd}&start_month={sm}&start_year={sy}&start_hour=0&start_min=0&end_day={ed}&end_month={em}&end_year={ey}&end_hour=23&end_min=59&output=ascii&odtype[]=uncorrected"
    url = url.format(sd=sd, sm=sm, sy=sy, ed=ed, em=em, ey=ey)
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html)
    pre = soup.find_all('pre')
    pre = pre[0].text
    pre = pre[pre.find('start_date_time'):]
    pre = pre.replace("start_date_time   1HCOR_E 1HUNCOR", "")
    f = open(nld['defaultdir']+"data/nmdb/tmp.txt", "w")
    f.write(pre)
    f.close()
    df = open(nld['defaultdir']+"data/nmdb/tmp.txt", "r")
    lines = df.readlines()
    df.close()
    lines = lines[1:]
    dfneut = pd.DataFrame(lines)
    dfneut = dfneut[0].str.split(";", n = 3, expand = True) 
    cols = ['DATE', 'COUNT', 'IGNORE']
    dfneut.columns = cols
    dates = dfneut['DATE']
    count = dfneut['COUNT']
    
    dfdict = dict(zip(dates, count))
    
    return dfdict
