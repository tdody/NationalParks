# -*- coding: utf-8 -*-
"""
Scrap National Parks info on Wikipedia
"""

from bs4 import BeautifulSoup
import urllib.request
import re
import os, sys
import pandas as pd
import json
sys.path.append('..')
import nationalparks as usnp
from dms2dec.dms_convert import dms2dec

NP_LINK = "https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true"

def scrap_park_data():
    """
    Extracts National Parks data from https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true
    
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

        ## clean park name
        np = np.replace('ʻ', '')
        np = np.replace('ā', 'a')
        np = np.replace('–', '-')

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

    ## read park units
    units = pd.read_csv("../scrapper/data/Parks.csv")
    
    ## merge
    parks = pd.merge(left=parks, right=units, left_on='index', right_on='parkname')
    del parks['parkname']

    ## read park websites
    websites = pd.read_csv('../scrapper/data/park_websites.csv')

    ## merge
    parks = pd.merge(left=parks, right=websites, on='parkunit')

    ## count photos
    parks['photo_count'] = parks['parkunit'].apply(get_photo_count)

    ## rename columns
    parks = parks.rename(columns={"index": "parkname"})

    ## get topo
    parks['boundaries'] = parks['parkunit'].apply(lambda x: get_geojson(x))
    parks['bbox'] = parks['parkunit'].apply(lambda x: get_bbox(x))

    return parks

def get_photo_count(parkunit):
    '''
    Return the number of photos used for the clustering
    '''
    photos = list(usnp.db.photos.find({'parkunit': parkunit}))
    df = pd.DataFrame(photos)
    return df._id.count()

def get_geojson(parkunit):
    path = '../scrapper/data/geojson/' + parkunit + '.geojson'
    if os.path.exists(path):
        with open(path, 'r') as file:
            geojson = file.read().replace('\n', '')
    else:
        raise Exception("geojson file not found.")
    return geojson

def get_bbox(parkunit):
    path = '../scrapper/data/topojson/' + parkunit + '.topojson'
    if os.path.exists(path):
        with open(path, 'r') as file:
            topojson = file.read()
            topojson = json.loads(topojson)
            bbox = {
                'min_longitude':topojson['bbox'][0],
                'min_latitude':topojson['bbox'][1],
                'max_longitude':topojson['bbox'][2],
                'max_latitude':topojson['bbox'][3]
                }
            return bbox
    else:
        raise Exception("topojson file not found.")

if __name__ == "__main__":
    df = scrap_park_data()