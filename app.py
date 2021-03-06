#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from platformdirs import AppDirs
from forms import *
import config
# from flask_migrate import Migrate
from forms import VenueForm, ArtistForm, ShowForm
from datetime import datetime
import sys
from sqlalchemy import func, true
import os
from models import Venue, Artist, Show


#------------------------------- App Config Start ---------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
# migrate = Migrate(app, db)

#------------------------------- App Config End ---------------------------------------------#


#----------------------------------- Filters Start -----------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------- Filters End -----------------------------------------#


#------------------------------------- Home route Start ---------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#------------------------------------- Home route End ---------------------------------------#



#  ------------------------------ Venues Start ----------------------------------

@app.route('/venues')
def venues():
  data = []
  areas = Venue.query.distinct('city', 'state').all()
  for area in areas:
    venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
    body = {
      'city': area.city,
      'state': area.state,
      'venues': [{'id': venue.id, 'name': venue.name, 'num_upcoming_show': venue.upcoming_shows} for venue in venues],
    }
    data.append(body)
  # print(json.dumps(body))
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  body = {}
  data = []
  venues = Venue.query.filter(func.lower(Venue.name).contains(search_term.lower())).all()
  for venue in venues:
    data.append({'id': venue.id, 'name': venue.name, 'num_upcoming_shows': venue.upcoming_shows})
  body['data'] = data
  body['count'] = len(venues)
  # print(json.dumps(data))
  return render_template('pages/search_venues.html', results=body, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.filter_by(id=venue_id).first().__dict__
  # print(json.dumps(data))

  past_shows = db.session.query(
    Venue, Show, Artist).filter(Venue.id == Show.venue_id)\
      .filter(Artist.id == Show.artist_id).filter(Show.start_time < datetime.now())\
        .filter(Venue.id == venue_id).all()
  # print(json.dumps(past_shows))

  upcoming_shows = db.session.query(Venue, Show, Artist)\
    .filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id)\
      .filter(Show.start_time > datetime.now()).filter(Venue.id == venue_id).all()
  
  # print(json.dumps(upcoming_shows))

  data['past_shows'] = [{
    'artist_id': artist.id, 'artist_name': artist.name,\
       'artist_image_link': artist.image_link, 'start_time': str(show.start_time)}\
          for (show, artist) in past_shows
  ]

  data['upcoming_shows'] = [
    {'artist_id': artist.id, 'artist_name': artist.name, 
    'artist_image_link': artist.image_link, 'start_time': str(show.start_time)}
     for (show, artist) in upcoming_shows
     ]

  data['past_show_count'] = len(data['past_shows'])
  data['upcoming_show_count'] = len(data['upcoming_shows'])
  # print(json.dumps(upcoming_shows))
  return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  # print(json.dumps(form))
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue = request.form.to_dict()
  error = True
  try:
    new_venue = Venue(name=venue['name'], city=venue['city'], state=venue['state'],
                      address=venue['address'], phone=venue['phone'], genres=request.form.getlist('genres'), 
                      facebook_link=venue['facebook_link'])
    db.session.add(new_venue)
    db.session.commit()
    # on success
    error = False
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    print(error)
  except Exception as e:
    db.session.rollback()
    # on fail
    print(error)
    flash('Venue ' + request.form['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).all()[0]
  # print(json.dumps(venue))
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = request.form.to_dict()
  error = True
  try:
    Venue.query.filter_by(id=venue_id).update(venue)
    Venue.query.filter_by(id=venue_id).update(
      dict(genres=request.form.getlist('genres'))
      )
    db.session.commit()
    # on success
    flash('Artist ' + venue['name'] + ' was successfully listed!')
    print(error = False)
  except Exception as e:
    db.session.rollback()
    # on fail
    print(error)
    flash('Artist ' + venue['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = True
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    # on success
    flash('Venue was successfully deleted!')
  except Exception as e:
    db.session.rollback()
    print(error)
    # on fail
    flash('Venue was not deleted, please try again or contact us!')
  finally:
    db.session.close()
  return None

#  ------------------------------ Venues End ----------------------------------


#  --------------------------------- Artists Start -------------------------------

@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  body = {}
  data = []
  artists = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower())).all()
  for artist in artists:
    data.append({'id': artist.id, 'name': artist.name, 
    'num_upcoming_shows': artist.upcoming_shows})
  body['data'] = data
  body['count'] = len(artists)
  # print(json.dumps(body))
  return render_template('pages/search_artists.html', results=body, 
  search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = Artist.query.filter_by(id=artist_id).first().__dict__

  past_shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id)\
    .filter(Artist.id == Show.artist_id).filter(Show.start_time < datetime.now())\
      .filter(Artist.id == artist_id).all()
  # print(past_shows.jsonify())

  upcoming_shows = db.session.query(Venue, Show, Artist)\
    .filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id)\
      .filter(Show.start_time > datetime.now()).filter(Artist.id == artist_id)\
        .all()
  
  data['past_shows'] = [
    {'venue_id': venue.id, 'venue_name': venue.name, 'venue_image_link': venue.image_link, 
    'start_time': str(show.start_time)} 
    for (venue, show, artist) in past_shows]
      
  # print(json.dumps(data))

  data['upcoming_shows'] = [{'venue_id': venue.id, 'venue_name': venue.name, 
  'venue_image_link': venue.image_link, 'start_time': str(show.start_time)} 
  for (venue, show) in upcoming_shows]
  # print(json.dumps(data))

  data['past_show_count'] = len(data['past_shows'])
  data['upcoming_show_count'] = len(data['upcoming_shows'])
  # print(json.dumps(data))
  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.filter_by(id=artist_id).all()[0]
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = request.form.to_dict()
  error = True
  try:
    Artist.query.filter_by(id=artist_id).update(artist)
    Artist.query.filter_by(id=artist_id).update(dict(genres=request.form.getlist
    ('genres')))
    db.session.commit()
    # on success
    flash('Artist ' + artist['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    # on fail
    print(error)
    flash('Artist ' + artist['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  artist = request.form.to_dict() 
  try:
    new_artist = Artist(
    name=artist['name'], city=artist['city'], 
    state=artist['state'], phone=artist['phone'], genres=request.form.getlist
    ('genres'), facebook_link=artist['facebook_link']
    )
    db.session.add(new_artist)
    db.session.commit()
    # on success
    flash('Artist ' + artist['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    # on fail
    flash('Artist ' + artist['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  --------------------------------- Artists Start -------------------------------


#  ------------------------------- Shows Start ---------------------------------

@app.route('/shows')
def shows():

  data = []

  shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id)\
    .filter(Artist.id == Show.artist_id).all()
  
  for (venue, show, artist) in shows:
    data.append({
      'venue_id': venue.id, 
      'venue_name': venue.name, 
      'artist_id': artist.id, 
      'artist_name': artist.name, 
      'artist_image_link': artist.image_link, 
      'start_time': str(show.start_time)
    })
  # print(json.dump(data))
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = true
  try:
    show = request.form.to_dict()
    start_time_format = datetime.strptime(show['start_time'], '%Y-%m-%d %H:%M:%S')
    new_show = Show(venue_id=show['venue_id'], artist_id=show['artist_id'], start_time=start_time_format)
    db.session.add(new_show)
    db.session.commit()
    # on success
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    app.logger.info(e)
    print(error)
    flash('Show was NOT successfully listed. Try again.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  ------------------------------- Shows Start ---------------------------------

#  ------------------------------- Error Handleing Start ---------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

#  ------------------------------- Error Handleing End ---------------------------------

#  ------------------------------- Debug Start ---------------------------------

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#  ------------------------------- Debug End ---------------------------------


#  -------------------------------  Start App ---------------------------------


# Default port is :5000
if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0')
