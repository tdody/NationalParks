# -*- coding: utf-8 -*-
"""
Parks and Park objects
"""

import nationalparks as np
import json
import folium
import shapely.geometry

class Parks():
    """
    Parks object
    """
    def __init__(self):
        pass

class Park():
    """
    Park object
    """
    def __init__(self, index):
        ## fetch park info
        result = np.db.parks.find_one({'parkunit':index})
        self.parkunit = index
        self.parkname = result['parkname']
        self.state = result['state']
        self.latitude = result['latitude']
        self.longitude = result['longitude']
        self.date = result['date']
        self.surface_acres = result['surface_acres']
        self.surface_km2 = result['surface_km2']
        self.visitors = result['visitors']
        self.description = result['description']
        ## photos
        self.boundaries = json.loads(result['boundaries'])
        self.bbox = result['bbox']
        self.bbox_points = self.__get_bbox_points()

    def in_park(self, photo):
        '''
        Returns true is the point (lon, lat) is contained within the park boundaries.
        This computation includes point that are within 1/500 of the length of the minimum
        of the width and the height of the park bounding box.
        This choice is made to limit the rejection of images that are located right on the boundary
        of the park
        '''
        ## create point of interest
        point = shapely.geometry.Point(photo['longitude'], photo['latitude'])
        ## set tolerance and result
        is_in = False
        tolerance = self.__get_tolerance()
        ## iterate over every polygons
        for polygon in self.boundaries['geometry']['coordinates']:
            ## create a temporary geojson dictionary
            data = {"type": "Polygon", "coordinates": [polygon]}
            shape = shapely.geometry.asShape(data)
            if shape.contains(point):
                return True
            if shape.distance(point) <= tolerance:
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
        query = {
            ''
        }