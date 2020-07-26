"""
Create connections to database
"""

from pymongo import MongoClient
from nationalparks import secrets as sec

class DB:
    '''
    Database class
    '''
    def __init__(self):
        '''
        Creates database engine
        '''
        self.client = MongoClient(
            "mongodb+srv://%s:%s@%s.mongodb.net/test?retryWrites=true&w=majority" % (sec.mongouser,
                                                                                     sec.mongopwd,
                                                                                     sec.mongohost),
            connect=False)
        
        ## database
        self.db = self.client.NationalParks

        ## collections
        self.parks = self.db.parks
        self.photos = self.db.photos

        self.dbscan = self.db.dbscan
        self.clusters = self.db.clusters