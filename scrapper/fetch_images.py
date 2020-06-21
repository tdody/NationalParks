# -*- coding: utf-8 -*-
"""
Retrieves images using Flickr API
"""
import sys, os
sys.path.append('..')
import flickrapi
import nationalparks
import pandas as pd
from nationalparks import logger

class FlickrImage():
    '''
    Flickr Image class
    Constructor:
        inputs:
            data from flickr.photos.search
    Methods:
        get_photo_url: return formatted url
        get_info: fetch detailed information about the image
    '''
    def __init__(self, data, flickr):
        self.id = data['id']
        self.owner = data['owner']
        self.secret = data['secret']
        self.server = data['server']
        self.farm = data['farm']
        self.title = data['title']
        self.owner = data['owner']
        self.flickr = flickr
        self.__get_info()
        self.__get_photo_url()
        
    def __get_photo_url(self):
        ## format url to image
        return "https://farm{0}.staticflickr.com/{1}/{2}_{3}.jpg".format(self.farm, self.server, self.id, self.secret)
        
    def __get_info(self):
        ## fetch info
        result = self.flickr.photos.getInfo(photo_id=self.id)
        ## parse info
        self.owner = result['photo']['owner']['username']
        self.dateposted = result['photo']['dates']['taken']
        self.tags = [x['raw'] for x in result['photo']['tags']['tag']]
        self.longitude = float(result['photo']['location']['longitude'])
        self.latitude = float(result['photo']['location']['latitude'])
        self.accuracy = result['photo']['location']['accuracy']
        self.context = result['photo']['location']['context']
        self.county = result['photo']['location']['county']['_content']
        self.region = result['photo']['location']['region']['_content']
        self.country = result['photo']['location']['country']['_content']
        self.neighbourhood = result['photo']['location']['neighbourhood']['_content']
        self.url = result['photo']['urls']['url'][0]['_content']

class FlickrImageFinder():
    def __init__(self, park_bboxes):
        self.flickr = flickrapi.FlickrAPI(nationalparks.secrets.api_key, nationalparks.secrets.api_secret, format='parsed-json')
        self.bboxes = park_bboxes

    def get_image_info(self, erase=True):
        '''

        '''
        ## iterate over all parks to get image info
        for parkunit in self.bboxes.keys():
            if os.path.exists('../scrapper/data/image_infos/' + parkunit + '_infos.csv') and not erase:
                pass
            else:
                ## import csv
                print('... fetching image ids for ' + parkunit)
                df = pd.read_csv('../scrapper/data/image_ids/' + parkunit + '_ids.csv')
                print('...    {} images found'.format(df.shape[0]))

                ## 


    def get_images_ids(self, erase=True):
        '''
        Fetch all the images that are located within the bbox of each park.
        Saves image id into a csv file.
        '''
        ## store image counts for log
        image_counts = {}

        ## iterate over all parks to get image ids
        for parkunit, bbox in self.bboxes.items():
            if os.path.exists('../scrapper/data/image_ids/' + parkunit + '_ids.csv') and not erase:
                image_counts[parkunit] = 'loaded'
                print('... existing data retrieved from {}_ids.csv'.format(parkunit))
            else:
                
                content = {}
                ## store number of total pages for API request
                total_page = 0
                ## cutoff datetime to extend request beyond 5000 images
                min_upload_date=0

                ## page 1
                ## retrieve number of pages, first cutoff, headers
                sets = self.flickr.photos.search(
                            privacy_filter=1,
                            has_geo=True,
                            bbox=bbox,
                            page=1,
                            sort='date-uploaded-asc')

                ## get number of pages
                total_page = sets['photos']['pages']

                ## get first cut-off (shift by 1 hour)
                min_upload_date=int(self.flickr.photos.getInfo(photo_id=sets['photos']['photo'][-1]['id'])['photo']['dates']['posted'])-60*60

                ## get header names
                columns = [x for x in sets['photos']['photo'][0].keys()]

                ## get image count
                print('... fetching image ids for ' + parkunit)

                for i in range(2,total_page+1):
                    sets = self.flickr.photos.search(
                        privacy_filter=1,
                        has_geo=True,
                        bbox=bbox,
                        page=1,
                        max_upload_date=str(min_upload_date),
                        sort='date-uploaded-asc')

                    if len(sets['photos']['photo'])==0:
                        break
                    
                    min_upload_date = int(self.flickr.photos.getInfo(photo_id=sets['photos']['photo'][-1]['id'])['photo']['dates']['posted'])-60*60

                    ## store images
                    for photo in sets['photos']['photo']:
                        content[photo['id']+"_"+photo['owner']+"_"+photo['secret']] = photo.values()
                    if i % 50 == 0:
                        print('   ... {0}/{1} pages completed'.format(i, total_page))
                image_counts[parkunit] = len(content)

                ## save to csv
                df = pd.DataFrame.from_dict(content, orient='index', columns=columns)
                df.to_csv('../scrapper/data/image_ids/' + parkunit + '_ids.csv')
                print('... {0} results saved in {1}_ids.csv'.format(len(content), parkunit))

        ## update logger
        logger.update_park_image_ids(image_counts)