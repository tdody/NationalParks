# -*- coding: utf-8 -*-
"""
Parks and Park objects
"""
import pymongo
import nationalparks as usnp
import json
import folium
import shapely.geometry
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
import re

class Parks():
    """
    Parks object
    """
    def __init__(self):
        pass

    def get_all_parkunits(self):
        '''
        Returns all park units (4 letters code).
        '''
        return usnp.db.parks.find().distinct('parkunit')

    def is_park_in_db(self, parkname):
        '''
        Return True if park name is in database.

        Input:
            parkname (string) e.g. Acadia National Park
        Output:
            True/False
        '''
        query = usnp.db.parks.find_one({'parkname':parkname})
        if query:
            return True
        else:
            return False

    def parkname_to_parkunit(self, parkname):
        '''
        Convert park name into park unit.
        
        Input:
            parkname (string) e.g. Acadia National Park
        Output:
            parkunit (string) e.g. acad
        '''
        query = usnp.db.parks.find_one({'parkname':parkname})
        if query:
            return query['parkunit']
        return None

class Park():
    """
    Park object
    """
    def __init__(self, parkunit):

        ## fetch park info
        result = usnp.db.parks.find_one({'parkunit':parkunit})
        self.parkunit = parkunit
        self.parkname = result['parkname']
        self.state = result['state']
        self.latitude = result['latitude']
        self.longitude = result['longitude']
        self.date = result['date']
        self.surface_acres = result['surface_acres']
        self.surface_km2 = result['surface_km2']
        self.visitors = result['visitors']
        self.description = result['description']

        ## boundaries
        self.boundaries = json.loads(result['boundaries'])
        self.bbox = result['bbox']
        self.bbox_points = self.__get_bbox_points()
        self.polygons = self.__get_polygons()

        ## websites
        self.official_website = result['official_website']
        self.alltrails_website = result['alltrails_website']
        
        ## photos
        self.photo_count = result['photo_count']
    
        ## clusters
        self.clusters = self.__get_clusters()

        ## dbscan
        self.dbscan = self.get_dbscan()

        ## idf
        self.idf = self.get_idf()
    
    def get_sw_ne(self):
        '''
        Returns list of south-west and north-east corner coordinates.
        
        Outputs:
            [ [min_lat, min_lon], [max_lat, max_lon] ]
        '''
        return [
            [self.bbox['min_latitude'],self.bbox['min_longitude']],
            [self.bbox['max_latitude'],self.bbox['max_longitude']]
            ]

    def __get_polygons(self):
        '''
        Formats the geojson used to store the park boundaries. This allows for the park boundaries to be
        plotted using folium.

        Output:
            formatted json file
        '''

        ## create storage for final output
        polygons = []

        ## if features key exists then iterate over polygons contained in each feature
        ## else only iterate over the polygons directly
        if "features" in self.boundaries:
            for group in self.boundaries['features']:
                for polygon in group['geometry']['coordinates']:
                    data = {"type": "Polygon", "coordinates": [polygon]}
                    polygons.append(shapely.geometry.asShape(data))
            return polygons
        else:
            for polygon in self.boundaries['geometry']['coordinates']:
                data = {"type": "Polygon", "coordinates": [polygon]}
                polygons.append(shapely.geometry.asShape(data))
            return polygons

    def in_park(self, photo):
        '''
        Returns true is the point (lon, lat) is contained within the park boundaries.
        This computation includes point that are within 1/500 of the length of the minimum
        of the width and the height of the park bounding box.
        This choice is made to limit the rejection of images that are located right on the boundary
        of the park.

        Input:
            photo (pandas DataFrame row) contains the longitude and latitude features
        
        Output:
            True/False whether photo coordinates are contained within the park
        '''
        ## create point of interest
        point = shapely.geometry.Point(float(photo['longitude']), float(photo['latitude']))
        ## set tolerance and result
        tolerance = self.__get_tolerance()
        ## iterate over every polygons
        for polygon in self.polygons:
            if polygon.contains(point):
                return True
            if polygon.distance(point) <= tolerance:
                return True
        return False

    def show_park(self):
        '''
        Returns a folium map of the park.
        The map includes the park boundaries (blue), the park bounding box (red), and the park center (pin).
        '''
        ## create map
        start_coords = (self.latitude, self.longitude)
        folium_map = folium.Map(
            location=start_coords,
            tiles='OpenStreetMap',
        )
        folium_map.fit_bounds(self.get_sw_ne())

        style_function = lambda x: {'fillColor': '#960808','fillOpacity': 0.1,'weight': 1.5, 'color':'#079305'}
        ## add park contour
        folium.GeoJson(
            self.boundaries,
            name='geojson',
            style_function=style_function
            ).add_to(folium_map)

        ## add markers
        for i, row in self.clusters.iterrows():
            if i<20:
                icon_path = "./app/static/img/" + str(row['rank']) + ".png"
                if row['rank']<=9:
                    size=(18,30)
                else:
                    size=(25,30)

                html = """<a href="{{ url_for('gallery') }}"> <button type="button" class="btn btn-primary">Small button</button></a>"""
                popup = folium.Popup(html)

                icon = folium.features.CustomIcon(icon_image=icon_path ,icon_size=size, icon_anchor=(size[0]//2, size[1]))
                folium.Marker([row['latitude'], row['longitude']], icon=icon).add_to(folium_map)
        
        return folium_map

    def __get_bbox_points(self):
        '''
        Returns a list of four tuples corresponding to the four corners of the park bounding box.
        [(T, L), (T, R), (B, R), (B, L)
        '''
        ## compute locations of the 4 corners
        upper_left=(self.bbox['max_latitude'], self.bbox['min_longitude'])
        upper_right=(self.bbox['max_latitude'], self.bbox['max_longitude'])
        lower_right=(self.bbox['min_latitude'], self.bbox['max_longitude'])
        lower_left=(self.bbox['min_latitude'], self.bbox['min_longitude'])
        return [upper_left, upper_right, lower_right, lower_left]

    def get_bbox_string(self):
        '''
        Format bbox coordinates by concatenation of the coordinates using a comma.
        '''
        return ', '.join([str(x) for x in self.bbox.values()])

    def __get_tolerance(self):
        '''
        Create a tolerance parameter used to estimate whether a photo was taken within the boundaries of the park.

        Output:
            float = min(park length (lat), park length (lon)) / 500
        '''
        lat_diff = self.bbox['max_latitude']-self.bbox['min_latitude']
        lon_diff = self.bbox['max_longitude']-self.bbox['min_longitude']
        return min(lat_diff, lon_diff) / 500.

    def get_photos(self):
        '''
        Queries photos of park from database.

        Output:
            pandas Dataframe containing all photos taken whithin the boundaries of the park.
        '''
        query = {
            'parkunit': self.parkunit,
        }

        photos = list(usnp.db.photos.find(query))
        
        df = pd.DataFrame(photos)
        df = df.set_index('id', drop=True)

        return df

    def get_dbscan(self):
        '''
        Queries DBSCAN of park from database.

        Output:
            Dictionary containing DBSCAN information.
        '''
        query = {
            'parkunit': self.parkunit,
        }

        photos = list(usnp.db.dbscan.find(query))
        
        dbscan = pd.DataFrame(photos).to_dict()

        return dbscan

    def get_top_photos(self, cluster_id, n_photos=50):
        '''
        Return the n_photos belonging to specified cluster sampled amongst the 500 most recent photos.

        Inputs:
            cluster_id (int) unique id of selected cluster
            n_photos (int) number of photos to be fetched
        Outputs:
            dictionary containing the information of the selected photos
        '''
        ## query MongoDB
        query = usnp.db.photos.find({
            "$and": [
                {'parkunit':self.parkunit},
                {'labels':cluster_id}
                ]
            }).sort('dateupload', pymongo.DESCENDING).limit(500)

        ## create dataframe
        photos = list(query)
        df = pd.DataFrame(photos)

        ## random sample
        df = df.sample(n=min(n_photos,500))
        df['title'] = df['title'].fillna("")

        ## create url
        df = df.set_index('id', drop=True)
        df['url'] = "https://farm" + df['farm'].astype('str') + ".staticflickr.com/" + df['server'].astype('str')+"/"+df.index.astype('str')+"_"+df['secret']+".jpg"

        return df.to_dict('records')

    def get_photo_count(self):
        '''
        Returns the number of photos taken in the park.
        '''
        return self.get_photos()['_id'].count()

    def plot_all_photos(self, color_clusters=True):
        '''
        Returns a plot showing the location of all the photos taken within the park boundaries.
        '''

        ## create figure
        fig, ax = plt.subplots(figsize=(12,16))

        ## get geojson data
        df_boundaries = gpd.read_file(os.path.join('../scrapper/data/geojson', self.parkunit + '.geojson'))
        df_boundaries.plot(alpha=0.2, ax=ax, color='grey')

        ## get photos
        df_photos = self.get_photos()
        top_labels = set(pd.Series(df_photos['labels']).value_counts().index.to_list())

        ## mapping label id with label rank
        df_labels = df_photos.groupby(['labels']).count()[['_id']].sort_values(['_id'],ascending=False).reset_index()
        df_labels.index +=1
        df_labels.index = "Rank:" + df_labels.index.astype(str) + " (" + df_labels['_id'].astype(str) + " photos)"
        mapping = {v:k for k,v in df_labels['labels'].to_dict().items()}

        df_photos['Cluster'] = df_photos['labels'].map(mapping)
        df_photos['rank'] = df_photos['Cluster'].str.extract('(\d+)\ \(').astype(int)

        df_photos = df_photos.sort_values(['rank'])

        flatui = ["#9b59b6", "#3498db", "#e74c3c",(0.4, 0.7607843137254902, 0.6470588235294118),
              (0.9882352941176471, 0.5529411764705883, 0.3843137254901961),
              (0.5529411764705883, 0.6274509803921569, 0.796078431372549),
              (0.9058823529411765, 0.5411764705882353, 0.7647058823529411),
              (0.6509803921568628, 0.8470588235294118, 0.32941176470588235),
              (1.0, 0.8509803921568627, 0.1843137254901961),
              (0.8980392156862745, 0.7686274509803922, 0.5803921568627451),
              (0.7019607843137254, 0.7019607843137254, 0.7019607843137254),
              (0.5019607843137255, 0.0, 0.5019607843137255),
              (0.0, 0.0, 0.5019607843137255),
              (0.7284890426758939, 0.15501730103806227, 0.1973856209150327),
              (0.21568627450980393, 0.47058823529411764, 0.7490196078431373),
              (0.996078431372549, 0.7019607843137254, 0.03137254901960784),
              (0.4823529411764706, 0.6980392156862745, 0.4549019607843137),
              (0.5098039215686274, 0.37254901960784315, 0.5294117647058824),
              (0.6423044349219739, 0.5497680051256467, 0.9582651433656727),
              (0.9603888539940703, 0.3814317878772117, 0.8683117650835491)]

        palette = sns.color_palette(flatui)

        ## plot photos
        if color_clusters:            
            sns.scatterplot(x='longitude', y='latitude', data=df_photos, hue='Cluster', alpha=0.3, linewidth=0, palette=palette[0:len(top_labels)])
        else:
            sns.scatterplot(x='longitude', y='latitude', data=df_photos, alpha=0.1, linewidth=0, ax=ax)
        ax.set_title(self.parkname + ": {} photos".format(df_photos.shape[0]), fontsize=15)

        plt.axis('off')

        plt.legend(bbox_to_anchor=(1.04,1), loc="upper left",fontsize=12)

        return ax

    def __get_clusters(self):
        '''
        Queries information of all clusters of the park.
        '''
        query = {
            'parkunit': self.parkunit,
        }

        clusters = list(usnp.db.clusters.find(query))
        df = pd.DataFrame(clusters)
        return df

    def convert_cluster_rank_to_id(self, rank):
        '''
        Convert a cluster rank into the cluster id.

        Input:
            rank (int) rank of the desired cluster
        Output:
            id (int) unique identifier for the selected cluster
        '''
        return self.clusters.query('rank=='+ str(rank))['labels'].values[0]

    def get_cluster_photos(self, cluster_rank):
        '''
        Queries photos of park from database.

        Input:
            cluster_rank (int) rank of the selected cluster
        Output:
            dataframe containing the cluster photos
        '''
        ## fetch cluster id
        cluster_id = self.convert_cluster_rank_to_id(cluster_rank)

        ## fetch photos associated to cluster
        query = {
            'parkunit': self.parkunit,
            'labels': int(cluster_id)
        }
        photos = list(usnp.db.photos.find(query))
        
        ## convert storage to dataframe
        df = pd.DataFrame(photos)
        df = df.set_index('id', drop=True)

        return df

    def get_top_tags(self, cluster_rank, top_count=20):
        '''
        Returns the most common tag for the selected cluster using tf-idf.

        Input:
            cluster_rank (int) rank of the selected cluster to explore
            top_count (int) number of tags to return
        Output:
            dictionary of top tags
                keys: (string) tags
                values: (float) tf-idf
        '''
        ## compute tf-idf
        tf_idf = self.tf_idf(cluster_rank)

        return sorted(tf_idf.items(), key=lambda x: x[1],reverse=False)[0:top_count]

    def get_idf(self):
        '''
        Returns the Inverse Document Frequency of all the tags assciated to a park.

        Output:
            dictionary of idf
                key = tag
                value = idf
        '''
        ## pattern
        pattern = re.compile("^[a-zA-Z]+$")

        ## get all photos
        df_all_photos = self.get_photos()

        ## cluster (document) count
        N = df_all_photos['labels'].nunique()

        ## find document occurrence
        df = {}

        ## cluster ids
        clusters = df_all_photos['labels'].unique()

        ## loop over each cluster and establish document occurrence
        for i in clusters:
            
            ## store unique tags
            word_set = set()
            for i, row in df_all_photos[(df_all_photos['labels']==i) & ~(df_all_photos['tags'].isnull())].iterrows():
                
                ## split tag list
                tag_list = row['tags'].split(' ')
                for tag in tag_list:
                    if pattern.match(tag):
                        word_set.add(tag)

            for w in word_set:
                if w in df.keys():
                    df[w] += 1
                else:
                    df[w] = 1

        ## compute idf
        for k, v in df.items():
            df[k] = N / float(df[k])

        return df

    def get_tf(self, cluster_rank, method='term frequency', K=0.5, max_df=0.007):
        '''
        Computes term frequency of the photo tags whithin a cluster.

        Inputs:
            cluster_rank (int)
            method (string)
                term frequency 
                log normalization
                double normalization
                double normalization K
            K (optional, int) normalization factor
        Output:
            dictionary of term-frequencies
                keys: tag (string)
                values: tf (float)
        '''
        ## pattern
        pattern = re.compile("^[a-zA-Z]+$")

        ## retrieve cluster photos
        df = self.get_cluster_photos(cluster_rank)

        ## storage and counter
        tag_counters = {}
        total = 0
        for i, row in df[df['tags'].notnull()].iterrows():

            ## create tag list
            tag_list = row['tags'].split(' ')
            tag_list = [x for x in tag_list if pattern.match(x)]

            if tag_list:
                for tag in tag_list:
                    if tag in tag_counters.keys():
                        tag_counters[tag] +=1
                    else:
                        tag_counters[tag] = 1

        ## count number of tags (used for frequency computation)
        total = sum([x for x in tag_counters.values()])

        ## clear when df is too high
        to_delete = []
        for k, v in tag_counters.items():
            if v / float(total) >= max_df:
                to_delete.append(k)

        ## clear tags with high frequency
        for k in to_delete:
            del tag_counters[k  ]

        total = sum([x for x in tag_counters.values()])

        if tag_counters == {}:
            return {}

        if method == 'term frequency':
            for k, v in tag_counters.items():
                tag_counters[k] /= total

        elif method == 'log normalization':
            for k, v in tag_counters.items():
                tag_counters[k] = np.log(1 + tag_counters[k])

        elif method == 'double normalization':
            max_f = float(max([x for x in tag_counters.values()]))
            for k, v in tag_counters.items():
                tag_counters[k] = 0.5 + 0.5 * tag_counters[k] / max_f

        elif method == 'double normalization K':
            max_f = float(max([x for x in tag_counters.values()]))
            for k, v in tag_counters.items():
                tag_counters[k] = K + (1 - K) * tag_counters[k] / max_f

        return tag_counters

    def tf_idf(self, cluster_rank):
        '''
        Compute tf-idf for the selected cluster rank.

        Input:
            cluster_rank (int) rank of the cluster to be explored
        Output:
            dictionary of tf-idf values
                keys: tags (string)
                values: tf-idf (float)
        '''
        tf = self.get_tf(cluster_rank, method='double normalization')

        # tf_idf storage
        tf_idf = {}

        for k in tf.keys():
            tf_idf[k] = tf[k] * np.log(float(self.idf[k]))

        return tf_idf