# -*- coding: utf-8 -*-
"""
Updates Tags Database
"""
import os, sys
sys.path.append('..')

import nationalparks as usnp
from nationalparks import database
from nationalparks import clusters
from nationalparks import parks

import pandas as pd
import json
import glob

def generate_tags():
    '''
    Generate most relevant tags
    '''
    
    ## create database clients
    DB = database.DB()

    ## get paths to csv
    cluster_path = '../scrapper/data/clusters'
    save_path  = '../scrapper/data/tfidf'
    cluster_files = glob.glob(cluster_path + '/*.csv')

    ## store dataframe for each data types
    clusters = []

    for cluster in cluster_files:
        df_cluster = pd.read_csv(cluster, index_col=0, header=0)
        df_cluster['top_tags'] = ''

        parkunit = df_cluster['parkunit'].values[0]
        park = usnp.Park(parkunit)

        df_cluster['top_tags'] = df_cluster['rank'].apply(lambda x: ";".join([x[0] for x in park.get_top_tags(x)]))

        print('... tf-idf computed for ' + cluster.split('/')[-1])

        ## save cluster dataframe
        df_cluster.to_csv(os.path.join(save_path, parkunit + ".csv"))

def update_database_clusters():
    '''
    Update MongoDB tables clusters
    '''
    
    ## create database clients
    DB = database.DB()

    ## get paths to csv
    cluster_path = '../scrapper/data/tfidf'
    cluster_files = glob.glob(cluster_path + '/*.csv')

    ## store dataframe for each data types
    clusters = []

    for cluster in cluster_files:
        df_cluster = pd.read_csv(cluster, index_col=None, header=0)

        clusters.append(df_cluster)

        print('... information retrieved for ' + cluster.split('/')[-1])

    ## compile info
    df_clusters = pd.concat(clusters, axis=0, ignore_index=True)
    print('... {:,} clusters found'.format(df_clusters.shape[0]))

    del df_clusters['Unnamed: 0']

    ## format dataframe into dictionary
    clusters = df_clusters.to_dict(orient='records') 

    ## clear existing content
    DB.clusters.delete_many({})

    ## update database
    DB.clusters.insert_many(clusters)

    print("... information updated")