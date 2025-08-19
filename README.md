![Yellowstone](https://github.com/tdody/NationalParks/blob/master/app/static/img/icon/banner.jpg)
# NationalParks

▶️ [Watch the video on YouTube](https://www.youtube.com/watch?v=JYDgPPAacCo)

## Motivation
The first National Park in the United States that I visited was Congaree National Park in South Carolina in 2018. I was immediately fascinated by the natural landscape and the vast biodiversity that I saw within the park. Since that time, I have visited a total of 5 National Parks across the US and I do not plan on stopping anytime soon.
Through this project, I will combine my passion for National Parks and machine learning to create a useful tool that will help those who wish to understand the National Park System better and explore America’s “Best Idea”.

## Goal
Yellowstone National Park was established as the first National Park in 1872. Since then, 61 Parks have been added to the US National Park System. The National Parks are the best illustration of what the American ecosystem has to offer. Every year, these locations welcome more than 80 millions visitors. The goal of usaparks.io is to transport visitors into the best locations of each park.
By using machine learning and clustering techniques, the application identifies the most photographed locations and gives the user the possibility to access some of these photographs. 
This application can be used as a tool to help you plan your upcoming trip to a National Park by showing you the most popular attractions or simply to give you virtual access to what these Parks have to offer.

## Data
The National Parks information was retrieved from the [Wikipedia](https://en.wikipedia.org/wiki/List_of_national_parks_of_the_United_States?oldformat=true) page In order to make this project feasible, we needed access to a large dataset of geolocalized photographs. The website data was scrapped using the popular python library [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/). Once the initial information has been gathered for all 62 National Parks, the park boundaries were obtained from the official National Park Service [Website](https://www.nps.gov/planyourvisit/maps.htm). The obtained Geojson files are used to identify pictures that are taken inside each park.
The photographs were obtained using the [Flickr API](https://www.flickr.com/services/api/). For each park, we create a bounding box using the maximum and minimum longitude and latitude obtained from the Geojson files.

## Clustering
In order to identify the most visited locations, we used Density-Based Spatial Clustering of Applications with Noise (DBSCAN). The longitude and latitude of each photograph are used to cluster the photos. The DBSCAN algorithm takes two parameters. The first one in the maximum distance used to search neighbors and the second one is the minimum number of neighbors to be contained within the maximum distance to be considered a cluster.

## Tags
When a photo is uploaded by a user on Flickr, tags can be added manually to the post. Tags consist of words that are relevant to the photo (location, photo content). The tags are compiled for each cluster and sorted using the Term Frequency–Inverse Document
Frequency (tf-idf). This summary of the most import tags is then provided on the cluster page to help describe the location corresponding to the cluster.

## Architecture
![Architecture](https://github.com/tdody/NationalParks/blob/master/app/static/img/misc/Architecture.png)
