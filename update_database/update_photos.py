# -*- coding: utf-8 -*-
"""
Updates Flickr database
"""
import os, sys
sys.path.append('..')

from nationalparks import database

import pandas as pd
import json
import glob

def update_photos():

    ## create database clients
    DB = database.DB()

    ## get paths to csv
    path = '../scrapper/data/filtered' # use your path
    all_files = glob.glob(path + '/*.csv')

    ## store dataframe for each park
    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0)

        ## add parkunit
        df['parkunit'] = filename.split('/')[-1].replace('.csv',"")

        ## drop unecessary features
        to_drop = [
            'Unnamed: 0','Unnamed: 0.1','ispublic',
            'isfriend','isfamily','accuracy',
            'place_id','woeid','originalsecret',
            'originalformat','machine_tags','geo_is_public',
            'geo_is_contact','geo_is_friend','geo_is_family'
        ]
        df = df.drop(to_drop, axis=1)

        li.append(df)

        print('... information retrieved for ' + filename)

    ## compile info
    df_photos = pd.concat(li, axis=0, ignore_index=True)
    print('... {:,} photos found'.format(df_photos.shape[0]))

    ## format dataframe into dictionary
    data = df_photos.to_dict(orient='records') 

    ## clear existing content
    DB.photos.delete_many({})

    ## update database
    DB.photos.insert_many(data)

if __name__ == "__main__":
    ## update parks
    update_photos()

    print("... Photos updated")