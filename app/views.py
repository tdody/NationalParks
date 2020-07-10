import os, sys
from flask import Flask, render_template, request, redirect, flash, redirect, url_for, Response
from app import app
import pymongo
import secrets as sec
import nationalparks as usnp
from wtforms import TextField, Form
import json

class SearchForm(Form):
    autocomp = TextField(None, id='city_autocomplete',description="TAD")


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = SearchForm(request.form)
    return render_template("find.html", message="", form=form)


@app.route('/about')
def about():
    return render_template("about.html", message="")


@app.route('/_autocomplete',methods=['GET'])
def autocomplete():
    parks = list(usnp.db.parks.find().distinct('parkname'))
    sorted(parks)
    return Response(json.dumps(parks), mimetype='application/json')


