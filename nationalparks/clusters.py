# -*- coding: utf-8 -*-
"""
Clusters object
"""
import pandas as pd
import nationalparks as usnp
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_samples, silhouette_score
import numpy

class Clusters():
    '''
    Train clustering model for all parks
    '''

    def __init__(self, parkunit):
        self.park = usnp.Park(parkunit)

    def train_DBSCAN(self, verbose=True):
        '''
        Performs DBSCAN clustering of images based on latitude and longitude.
        '''
        if verbose: print("... " + self.park.parkname + " (" + self.park.parkunit + ")")
        ## get all photos
        df_photos = self.park.get_photos()
        ## sort by latitude and longitude
        df_photos = df_photos.sort_values(by=['longitude', 'latitude'])
        ## extract latitude and longitude
        df_geo = df_photos[['latitude', 'longitude']]
        ## compute differences
        diff = df_geo.diff()
        ## compute euclidian distance
        diff['distance'] = (diff['latitude']**2 + diff['longitude']**2) ** 0.5
        ## format dataframe
        diff = diff.rename(columns={'latitude':"latitude_diff", 'longitude':'longitude_diff'})
        ## merge data
        df_geo = pd.concat([df_photos[df_photos.columns.difference(['latitude', 'longitude'])], df_geo, diff], axis=1)

        ## HYPER-PARAMETER TUNING
        ## eps
        best_score = -1
        best_eps = 0
        ## create a set of candidate values for eps based on quantile distribution of the distance between points
        range_eps = df_geo[~df_geo['distance'].isnull()]['distance'].quantile([0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.675,0.70,0.75,0.8,0.825,0.85,0.875,0.90,0.925,0.95,0.975,0.98,0.99,0.995])
        
        if df_geo.shape[0]<=100:
            min_cluster_count = 2
            max_cluster_count = 5
        elif df_geo.shape[0]<=1000:
            min_cluster_count = 5
            max_cluster_count = 50
        elif df_geo.shape[0]<=10000:
            min_cluster_count= 10
            max_cluster_count = 500
        else:
            min_cluster_count = 10
            max_cluster_count = 500        
        
        for i in range_eps:
            if i==0:
                continue
            if i > 0.4 * df_geo['distance'].max():
                continue
            ## create and train DBSCAN
            db = DBSCAN(eps=i, min_samples=5, n_jobs=-1).fit(df_geo[['latitude', 'longitude']]) 
            labels = db.labels_
            ## compute silhouette score
            if len(set(labels))>=min_cluster_count and len(set(labels))<=max_cluster_count:
                if min_cluster_count==1 and len(set(labels))==1 and best_score==-1:
                    print("   For eps value = "+str(i), "\n   Number of clusters: {}".format(len(set(labels))))
                    best_eps = i
                else:
                    silhouette_avg = silhouette_score(df_geo[['longitude', 'latitude']], labels)
                    print("   For eps value: "+str(i), ", quantile: {:.5f}".format(i), "\n      Number of clusters: {}".format(len(set(labels))),
                    "\n      Avg silhouette score is: {:.4f}".format(silhouette_avg))
                if best_score < silhouette_avg:
                    print("      => Improved")
                    best_score = silhouette_avg
                    best_eps = i
            else:
                print("   eps: {:.5f} out of cluster bounds".format(i))
        
        ## min_samples
        best_score = -1
        best_min_samples = 0
        min_samples = [2,3,5,6,7,8,9,10,12,14,16,18,20]
        for i in min_samples:
            ## create and train DBSCAN
            db = DBSCAN(eps=best_eps, min_samples=i, n_jobs=-1).fit(df_geo[['longitude', 'latitude']])
            labels = db.labels_
            ## compute silhouette score
            if len(set(labels)) >= min_cluster_count:
                if min_cluster_count==1 and len(set(labels))==1 and best_score==-1 and best_min_samples==0:
                    print("   For eps value = "+str(i), "\n   Number of clusters: {}".format(len(set(labels))))
                    best_min_samples=i
                else:
                    silhouette_avg = silhouette_score(df_geo[['longitude', 'latitude']], labels)
                    print("   For min_sample value = "+str(i), "\n      Number of clusters: {}".format(len(set(labels))),
                    "\n      Avg silhouette score is: {:.4f}".format(silhouette_avg))
                    if best_score < silhouette_avg and len(set(labels))>=min_cluster_count:
                        print("      => Improved")
                        best_score = silhouette_avg
                        best_min_samples = i
        
        ## train final DBSCAN
        db = DBSCAN(eps=best_eps, min_samples=best_min_samples, n_jobs=-1).fit(df_geo[['longitude', 'latitude']])

        ## get core samples
        core_sample_mask = numpy.zeros_like(db.labels_, dtype=bool)
        core_sample_mask[db.core_sample_indices_] = True
        df_geo['core'] = core_sample_mask
        df_geo['labels'] = db.labels_

        del df_geo['distance']
        del df_geo['latitude_diff']
        del df_geo['longitude_diff']

        return df_geo, db.labels_.max() + 1, best_eps, best_min_samples

    def jaccard_index(tags_cluster_1, tags_cluster_2):
        '''
        Returns the Jaccard Similarity Index between two cluster's tags
        
        Inputs:
            tags_cluster_1: list of tags (with potential duplicates) associated to cluster_1
            tags_cluster_2: list of tags (with potential duplicates) associated to cluster_2
        Outputs:
            Jaccard Similarity Index between two cluster's tags
        '''
        
        if len(set(tags_cluster_1)) == 0 and len(set(tags_cluster_2)) == 0:
            return 0
        else:
            shared = len(set(tags_cluster_1).intersection(tags_cluster_2))
            return shared / float(len(set(tags_cluster_1)) + len(set(tags_cluster_2)) - shared)

    def get_clusters(self):
        '''
        Queries clusters of park from database
        '''
        query = {
            'parkunit': self.parkunit,
        }

        my_clusters = list(usnp.db.clusters.find(query))
        df = pd.DataFrame(my_clusters)
        df = df.set_index('id', drop=True)
        return df

