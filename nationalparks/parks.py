# -*- coding: utf-8 -*-
"""
Parks and Park objects
"""

import nationalparks as usnp
import json
import folium
import shapely.geometry
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import os

class Parks():
    """
    Parks object
    """
    def __init__(self):
        pass

    def get_all_parkunits(self):
        return usnp.db.parks.find().distinct('parkunit')

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
        ## photos
    
    def __get_polygons(self):
        '''
        '''
        polygons = []

        if "features" in self.boundaries:
            i = 0
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
        of the park
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
        m = folium.Map(location=[self.latitude, self.longitude])
        ## add boundaries
        folium.GeoJson(
            self.boundaries,
            name='geojson'
            ).add_to(m)
        ## add bounding box
        folium.Rectangle(
            bounds=self.__get_bbox_points(),
                 color='#ff7800',
                 fill=False,
                 fill_opacity=0.2
                 ).add_to(m)
        ## add marker
        folium.Marker([self.latitude, self.longitude], popup=self.parkname, tooltip=self.parkname).add_to(m)
        folium.LayerControl().add_to(m)
        return m

    def __get_bbox_points(self):
        '''
        Returns a list of four turples corresponding to the four corners of the park bounding box.
        [(T, L), (T, R), (B, R), (B, L)
        '''
        ## compute locations of the 4 corners
        upper_left=(self.bbox['max_latitude'], self.bbox['min_longitude'])
        upper_right=(self.bbox['max_latitude'], self.bbox['max_longitude'])
        lower_right=(self.bbox['min_latitude'], self.bbox['max_longitude'])
        lower_left=(self.bbox['min_latitude'], self.bbox['min_longitude'])
        return [upper_left, upper_right, lower_right, lower_left]

    def get_bbox_string(self):
        return ', '.join([str(x) for x in self.bbox.values()])

    def __get_tolerance(self):
        lat_diff = self.bbox['max_latitude']-self.bbox['min_latitude']
        lon_diff = self.bbox['max_longitude']-self.bbox['min_longitude']
        return min(lat_diff, lon_diff) / 500.

    def get_photos(self):
        '''
        Queries photos of park from database
        '''
        query = {
            'parkunit': self.parkunit,
        }

        photos = list(usnp.db.photos.find(query))
        
        df = pd.DataFrame(photos)
        df = df.set_index('id', drop=True)

        return df

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
        fig, ax = plt.subplots(figsize=(12,12))

        ## get geojson data
        df_boundaries = gpd.read_file(os.path.join('../scrapper/data/geojson', self.parkunit + '.geojson'))
        df_boundaries.plot(alpha=0.2, ax=ax, color='grey')

        ## get photos
        df_photos = self.get_photos()
        top_labels = set(pd.Series(df_photos['labels']).value_counts().index.to_list())

        ## plot photos
        if color_clusters:
            sns.scatterplot(x='longitude', y='latitude', data=df_photos, hue='labels', alpha=0.3, linewidth=0, palette=sns.color_palette("muted", n_colors=len(top_labels)))
        else:
            sns.scatterplot(x='longitude', y='latitude', data=df_photos, alpha=0.1, linewidth=0, ax=ax)
        ax.set_title(self.parkname + ": {} photos".format(df_photos.shape[0]))

        return ax


