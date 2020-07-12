import os, sys
from flask import Flask, render_template, request, redirect, flash, redirect, url_for, Response
from app import app
import pymongo
import secrets as sec
import nationalparks as usnp
from wtforms import TextField, Form
import json
import folium

class SearchForm(Form):
    autocomp = TextField(None, id='park_autocomplete', description="TAD")

@app.route('/', methods=['GET', 'POST'])
def home():
    form = SearchForm(request.form)
    return render_template("find.html", message="", form=form)

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/explore', methods=['GET', 'POST'])
def explore_park():

    ## retrieve infos
    parkname = request.args.get('autocomp')

    ## validate input (i.e. check parkname in DB)
    if not usnp.parks.is_park_in_db(parkname):
        form = SearchForm(request.form)
        return render_template('find.html', message="Enter a valid park name.", form=form)

    ## create park object
    parkunit = usnp.parks.parkname_to_parkunit(parkname)
    park = usnp.Park(parkunit)
    photo_count = park.photo_count

    ## get cluster info
    if photo_count > 0:
        clusters = park.clusters
        cluster_count = clusters.shape[0]
    else:
        clusters, cluster_count = 0, 0

    message = 'Click a scene marker to explore.'
    if cluster_count == 0:
        message = 'There are no locations to explore for this park.'

    ## FOLIUM MAP
    start_coords = (park.latitude, park.longitude)
    folium_map = folium.Map(
        location=start_coords,
        tiles='OpenStreetMap',
    )
    ## OpenStreetMap, Stamen Terrain
    folium_map.fit_bounds(park.get_sw_ne())

    style_function = lambda x: {'fillColor': '#960808','fillOpacity': 0.2,'weight': 1, 'color':'#960808'}
    ## add park contour
    folium.GeoJson(
        park.boundaries,
        name='geojson',
        style_function=style_function
        ).add_to(folium_map)

    ## add markers
    for i, row in park.clusters.iterrows():
        folium.Marker([row['latitude'], row['longitude']], popup=park.parkname, icon=folium.Icon(color='lightgray', icon='home', prefix='fa')).add_to(folium_map)

    folium_map.save('app/templates/map.html')

    return render_template(
        "explore.html",
        parkname=parkname,
        state=park.state,
        parkunit=parkunit,
        photo_count="{:,}".format(photo_count),
        cluster_count=cluster_count,
        description=park.description,
        park_website=park.official_website,
        park_trails=park.alltrails_website,
        message=message)


@app.route('/about')
def about():
    return render_template("about.html", message="")


@app.route('/_autocomplete',methods=['GET'])
def autocomplete():
    parks = list(usnp.db.parks.find().distinct('parkname'))
    sorted(parks)
    return Response(json.dumps(parks), mimetype='application/json')


