# -*- coding: utf-8 -*-
"""
Clusters object
"""
import pandas as pd
import nationalparks as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_samples, silhouette_score
import numpy

'''

'''



class Clusters():
    def __init__(self, parkunit):
        self.park = np.parks.Park(parkunit)

    def DBSCAN(self):
        pass

    def train_DBSCAN(self, verbose=True):
        '''
        Performs DBSCAN clustering of images based on latitude and longitude
        '''
        if verbose: print("..." + self.park.parkname)
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
        range_eps = df_geo[~df_geo['distance'].isnull()]['distance'].quantile([0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.675,0.70,0.75])
        for i in range_eps:
            if i==0:
                continue
            if i > 0.4 * df_geo['distance'].max():
                continue
            ## create and train DBSCAN
            db = DBSCAN(eps=i, min_samples=5, n_jobs=-1).fit(df_geo[['latitude', 'longitude']]) 
            labels = db.labels_
            ## compute silhouette score
            silhouette_avg = silhouette_score(df_geo[['longitude', 'latitude']], labels)
            if verbose: print("   ...eps={:.5f}, silhouette={:.3f}, cluster count={}".format(i,silhouette_avg,len(set(labels))))
            if best_score < silhouette_avg and len(set(labels))>=40:
                best_score = silhouette_avg
                best_eps = i
        
        ## min_samples
        best_score = -1
        best_min_samples = 0
        min_samples = [2,3,5,6,7,8,9,10,12,14,16,18,20]
        for i in min_samples:
            ## create and train DBSCAN
            db = DBSCAN(eps=best_eps, min_samples=i, n_jobs=-1).fit(df_geo[['longitude', 'latitude']])
            labels = db.labels_
            ## compute silhouette score
            silhouette_avg = silhouette_score(df_geo[['longitude', 'latitude']], labels)
            if verbose: print("   ...eps={:.5f}, min samples={}, silhouette={:.3f}, cluster count={}".format(best_eps,i,silhouette_avg,len(set(labels))))
            if best_score < silhouette_avg and len(set(labels))>=40:
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

        return df_geo, db.labels_.max() + 1



    def get_DBSCAN():
        pass
    

