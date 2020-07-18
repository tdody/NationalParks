# -*- coding: utf-8 -*-
"""
Updates Cluster Database
"""
import os, sys
sys.path.append('..')

from nationalparks import database
from nationalparks import clusters
from nationalparks import parks

import pandas as pd
import json
import glob

def create_clusters(verbose=True, erase=True):
    '''
    Read image data from MongoDB, for each park perform DBSCAN with hyper-parameter tuning.
    Save csv files (clusters, dbscan, photos)
    '''
    ## create database clients
    DB = database.DB()

    ## store dataframe for each park
    #data_clusters = []
    #data_dbscan = []
    #data_photos = []

    ## check if locations exists
    cluster_path = '../scrapper/data/clusters'
    dbscan_path = '../scrapper/data/dbscan'
    photo_path = '../scrapper/data/photo_clusters'
    if not os.path.exists(cluster_path):
        os.mkdir(cluster_path)
    if not os.path.exists(dbscan_path):
        os.mkdir(dbscan_path)
    if not os.path.exists(photo_path):
        os.mkdir(photo_path)

    ## train DBSCAN for each park
    for parkunit in parks.Parks().get_all_parkunits():

        ## check if data already exists
        train_dbscan = False
        if not os.path.exists(os.path.join(cluster_path, parkunit + '.csv')):
            train_dbscan = True
        if not os.path.exists(os.path.join(dbscan_path, parkunit + '.csv')):
            train_dbscan = True
        if not os.path.exists(os.path.join(photo_path, parkunit + '.csv')):
            train_dbscan = True

        if train_dbscan:

            ## create clusters
            cluster = clusters.Clusters(parkunit)

            ## train DBSCAN
            df_geo, n_clusters, best_eps, best_min_samples = cluster.train_DBSCAN(verbose=verbose)

            ## store info about dbscan
            dbscan = pd.DataFrame([{'parkunit':parkunit, 'n_clusters':n_clusters+1, 'eps':best_eps, 'min_samples':best_min_samples}])
            dbscan.to_csv(os.path.join(dbscan_path, parkunit + ".csv"))

            ## store info about clusters
            cluster = df_geo[['latitude', 'longitude', 'labels', '_id']].groupby(['labels']).agg({'latitude':'mean', 'longitude':'mean', '_id':'count'}).reset_index()

            ## get cluster id and sort by popularity
            labels_by_popularity = df_geo[['_id', 'labels']].groupby(['labels']).count().sort_values(by='_id', ascending=False).index 
            labels_by_popularity = labels_by_popularity[labels_by_popularity!=-1]
            top_20 = labels_by_popularity[0:20]
            labels_by_popularity = dict(zip(labels_by_popularity,range(1,len(labels_by_popularity)+1)))

            ## create popularity feature
            cluster['top_20'] = cluster['labels'].isin(top_20)
            cluster['parkunit'] = parkunit
            cluster['rank'] = cluster['labels'].map(labels_by_popularity)
            cluster = cluster[~cluster['rank'].isnull()].reset_index()
            cluster['rank'] = cluster['rank'].astype(int)
            cluster = cluster[cluster['top_20']]
            cluster = cluster.rename(columns={"_id":"photo_count"})

            ## save cluster dataframe
            cluster.to_csv(os.path.join(cluster_path, parkunit + ".csv"))

            ## remove some photos
            df_geo = df_geo[df_geo['labels'].isin(top_20)]
            df_geo.to_csv(os.path.join(photo_path, parkunit + ".csv"))
        
        else:
            if verbose:
                print("...data already exists for " + parkunit)

def update_database_clusters():
    
    ## create database clients
    DB = database.DB()

    ## get paths to csv
    cluster_path = '../scrapper/data/clusters'
    dbscan_path = '../scrapper/data/dbscan'
    photo_path = '../scrapper/data/photo_clusters'
    cluster_files = glob.glob(cluster_path + '/*.csv')
    dbscan_files = glob.glob(dbscan_path + '/*.csv')
    photo_files = glob.glob(photo_path + '/*.csv')

    ## store dataframe for each data types
    clusters = []
    dbscans = []
    photos = []

    for (cluster, dbscan, photo) in zip(cluster_files, dbscan_files, photo_files):
        df_cluster = pd.read_csv(cluster, index_col=None, header=0)
        df_dbscan = pd.read_csv(dbscan, index_col=None, header=0)
        df_photo = pd.read_csv(photo, index_col=None, header=0)

        clusters.append(df_cluster)
        dbscans.append(df_dbscan)
        photos.append(df_photo)

        print('... information retrieved for ' + cluster.split('/')[-1])

    ## compile info
    df_clusters = pd.concat(clusters, axis=0, ignore_index=True)
    df_dbscans = pd.concat(dbscans, axis=0, ignore_index=True)
    df_photos = pd.concat(photos, axis=0, ignore_index=True)
    print('... {:,} clusters found'.format(df_clusters.shape[0]))
    print('... {:,} dbscans found'.format(df_dbscans.shape[0]))
    print('... {:,} photos found'.format(df_photos.shape[0]))

    del df_clusters['Unnamed: 0']
    del df_dbscans['Unnamed: 0']
    del df_clusters['index']

    ## format dataframe into dictionary
    clusters = df_clusters.to_dict(orient='records') 
    dbscans = df_dbscans.to_dict(orient='records') 
    photos = df_photos.to_dict(orient='records') 

    ## clear existing content
    DB.clusters.delete_many({})
    DB.dbscan.delete_many({})
    DB.photos.delete_many({})

    ## update database
    DB.clusters.insert_many(clusters)
    DB.dbscan.insert_many(dbscans)
    DB.photos.insert_many(photos)

    print("... information updated")