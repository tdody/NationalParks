# -*- coding: utf-8 -*-
"""
Scrap National Parks info on Wikipedia
"""

from bs4 import BeautifulSoup
import urllib.request
import re
import os, sys
import pandas as pd
sys.path.append('..')
from dms2dec.dms_convert import dms2dec

NP_LINK = "https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true"

def scrap_park_data():
    """
    Extract National Parks data from https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true
    
    Saves a csv file containing:
        - Park name
        - State
        - Latitude and Longitude
        - Surface (acres km2)
        - Number of visitors
        - Description
    """

    ## load article, turn into soup and get the <table>s.
    page = urllib.request.urlopen(NP_LINK)
    
    ## create soup
    soup = BeautifulSoup(page, 'html.parser')
    
    ## find all tables
    np_table = soup.find_all('table', class_='sortable')[0]
    
    parks = []
    data = {}
    ## find table header
    
    ## find table row (tr)
    tbody = np_table.find_all("tbody")[0]
    trs = tbody.find_all("tr")
    
    ## skip first tr since it contains the headers
    for i in range(1,len(trs)):
    
        ## extract row content
        tr = trs[i]
        
        ## find park name
        np = tr.find_all("a")[0].get('title')
        parks.append(np)
        data[np] = {}
    
        ## find park data
        tds = tr.find_all("td")
    
        ## first td: image
        ## skip
        
        ## state + coordinates
        ## offset by one if first cell is td
        if len(tds)==6:
            offset = 1
        else:
            offset=2
    
        ## extract state, latitude, and longitude
        data[np]["state"] = tds[offset].find("a").get('title')
        lat = tds[offset].find("span",{"class":"latitude"}).text
        long = tds[offset].find("span",{"class":"longitude"}).text
        data[np]["latitude"] = dms2dec(lat) 
        data[np]["longitude"] = dms2dec(long)
    
        ## date
        data[np]["date"] = tds[offset+1].find("span").text
        
        ## area
        surface = re.findall(r'(\d*\,?\d*\,?\d+\.?\d*)\s', tds[offset+2].text)
        data[np]["surface_acres"] = float(surface[0].replace(',',""))
        data[np]["surface_km2"]  = float(surface[1].replace(',',""))
        
        ## visitors
        data[np]["visitors"] = float(re.search(r'(\d*\,?\d*\,?\d+\.?\d*)', tds[offset+3].text)[0].replace(",",""))

        ## description
        description = re.sub(r'\[?\(?\d+\)?\]?', '', tds[offset+4].text.strip())
        data[np]["description"] = description
        
    ## create dataframe
    parks = pd.DataFrame(data).T.reset_index()

    return parks