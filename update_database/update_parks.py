# -*- coding: utf-8 -*-
"""
Updates National Parks database
"""
import os, sys
sys.path.append('..')

from nationalparks import database
from scrapper import scrap_parks

import pandas as pd
import json

def update_parks():

    ## create database clients
    DB = database.DB()

    ## fetch parks info
    df_parks = scrap_parks.scrap_park_data()
    records = json.loads(df_parks.T.to_json()).values()

    ## clear existing content
    DB.parks.delete_many({})

    ## update database
    ## index, state, latitude, longitude, date, surface_acres, surface_km2, visitors, description
    DB.parks.insert_many(records)
    

if __name__ == "__main__":
    ## update parks
    update_parks()

    print("... Park data updated")