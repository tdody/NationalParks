# -*- coding: utf-8 -*-
"""
Parks and Park objects
"""

import nationalparks as np

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
        result = np.db.find_one({'parkcode':parkcode})
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
        self.boundaries = result['boundaries']

    def show_park(self):
        
    
    def photos(self):
        query = {
            ''
        }