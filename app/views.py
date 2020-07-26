import os, sys
from flask import Flask, render_template, request, redirect, flash, redirect, url_for, Response
from app import app
import pymongo
import secrets as sec
import nationalparks as usnp
from wtforms import TextField, Form, SelectField
import json
import folium

class SearchForm(Form):
    autocomp = TextField(None, id='park_autocomplete', description="TAD")

class SelectForm(Form):
    locationSelect = SelectField('location', choices=[])

@app.route('/', methods=['GET', 'POST'])
def home():
    form = SearchForm(request.form)
    return render_template("find.html", message="", form=form)

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/explore', methods=['GET'])
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

    ## map
    folium_map = park.show_park()
    folium_map.save('app/templates/map.html')

    ## locations
    form = SelectForm()
    form.locationSelect.choices = [(parkname + '//' + str(i+1), 'Scene ' + str(i+1)) for i in range(cluster_count)]

    ## selected clusters
    cluster_rank = 1

    ## get cluster id
    cluster_id = clusters.loc[clusters['rank']==cluster_rank,'labels'].to_numpy()[0]

    ## photos
    photos = park.get_top_photos(int(cluster_id), n_photos=25)

    ## tf-idf
    tags = park.clusters[park.clusters['rank']==cluster_rank]['top_tags'].values[0]
    if tags:
        tags = tags.split(";")

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
        message=message,
        form=form,
        samples=photos,
        cluster_rank=cluster_rank,
        tags=tags)

@app.route('/update_cluster', methods=['GET','POST'])
def update_cluster():
    results = request.args.get('locationSelect')
    results = results.split("//")
    parkname = results[0]
    cluster_rank = int(results[1])

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

    ## map
    folium_map = park.show_park()
    folium_map.save('app/templates/map.html')

    ## locations
    form = SelectForm()
    form.locationSelect.choices = [(parkname + '//' + str(i+1), 'Scene ' + str(i+1)) for i in range(cluster_count)]

    ## get cluster id
    cluster_id = clusters.loc[clusters['rank']==cluster_rank,'labels'].to_numpy()[0]

    ## photos
    photos = park.get_top_photos(int(cluster_id), n_photos=25)

    ## tf-idf
    tags = park.clusters[park.clusters['rank']==cluster_rank]['top_tags'].values[0]
    if tags:
        tags = tags.split(";")

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
        message=message,
        form=form,
        samples=photos,
        cluster_rank=cluster_rank,
        tags=tags)

@app.route('/gallery')
def gallery():
    return render_template('find.html')

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/model')
def model():
    parks = list(usnp.db.parks.find({}, { "parkname": 1, "_id":0, "parkunit":1, "state":1}).sort("parkname"))
    
    for park in parks:
        park['url'] = "img/tiles/" + park['parkunit'] + ".jpg"
    return render_template("model.html", parks=parks)

@app.route('/modeldetails', methods=['GET', 'POST'])
def model_details():
    parkunit = request.args.get('parkunit')
    park = usnp.db.parks.find_one({'parkunit':parkunit})
    park = usnp.Park(parkunit)
    return render_template("modeldetails.html", park=park)

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/_autocomplete',methods=['GET'])
def autocomplete():
    parks = list(usnp.db.parks.find().distinct('parkname'))
    sorted(parks)
    return Response(json.dumps(parks), mimetype='application/json')