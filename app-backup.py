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
from flask_migrate import Migrate
from forms import VenueForm, ArtistForm, ShowForm
from datetime import datetime
import sys
from sqlalchemy import func
import os
from models import Venue, Artist, Show


#------------------------------- App Config Start ---------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#------------------------------- App Config End ---------------------------------------------#



# #-------------------------------------- Models Start --------------------------------------#

# class Venue(db.Model):
#   __tablename__ = 'Venue'
#   id = db.Column(db.Integer, primary_key=True)
#   name = db.Column(db.String)
#   city = db.Column(db.String(120))
#   state = db.Column(db.String(120))
#   address = db.Column(db.String(120))
#   phone = db.Column(db.String(120))
#   image_link = db.Column(db.String(500))
#   facebook_link = db.Column(db.String(120))
#   genres = db.Column(db.ARRAY(db.String(200)))
#   seeking_talent = db.Column(db.Boolean)
#   seeking_description = db.Column(db.String(500))
#   website = db.Column(db.String(120))
#   show = db.relationship('Show', backref='venue', lazy=True)

#   def upcoming_shows():
#     shows = db.session.query(Venue.id, Venue.name).join(Show).filter(Show.start_time > datetime.now).count()

#   def past_shows():
#     shows = db.session.query(Venue.id, Venue.name).join(Show).filter(Show.start_time < datetime.now).count()


#   def __repr__(self):
#     return f'<id: {self.id}, name: {self.name}, state: {self.state}>'

# class Artist(db.Model):
#   __tablename__ = 'Artist'
#   id = db.Column(db.Integer, primary_key=True)
#   name = db.Column(db.String)
#   city = db.Column(db.String(120))
#   state = db.Column(db.String(120))
#   phone = db.Column(db.String(120))
#   genres = db.Column(db.ARRAY(db.String(200)))
#   seeking_venue = db.Column(db.Boolean)
#   seeking_description = db.Column(db.String(500))
#   website = db.Column(db.String(120))
#   image_link = db.Column(db.String(500))
#   facebook_link = db.Column(db.String(120))
#   show = db.relationship('Show', backref='artist', lazy=True)

#   def __repr__(self):
#     return f'<id: {self.id}, name: {self.name}, state: {self.city}>'

# class Show(db.Model):
#   __tablename__ = 'Show'
#   id = db.Column(db.Integer, primary_key=True)
#   venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
#   artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
#   start_time = db.Column(db.DateTime)

#   def __repr__(self):
#     return f'<id: {self.id}, venue_id: {self.venue_id}, artist_id: {self.artist_id}, time: {self.start_time}>'

# #-------------------------------------- Models End --------------------------------------#



#----------------------------------- Filters Start -----------------------------------------#

# def format_datetime(value, format='medium'):
#   date = dateutil.parser.parse(value)
#   if format == 'full':
#       format="EEEE MMMM, d, y 'at' h:mma"
#   elif format == 'medium':
#       format="EE MM, dd, y h:mma"
#   return babel.dates.format_datetime(date, format)

# app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------- Filters End -----------------------------------------#


#------------------------------------- Controllers Start ---------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#------------------------------------- Controllers End ---------------------------------------#



#  ------------------------------ Venues Start ----------------------------------

@app.route('/venues')
def venues():
  data = []
  areas = Venue.query.distinct('city', 'state').all()
  for area in areas:
    venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
    record = {
      'city': area.city,
      'state': area.state,
      'venues': [{'id': venue.id, 'name': venue.name, 'num_upcoming_show': venue.upcoming_shows} for venue in venues],
    }
    data.append(record)
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  response = {}
  data = []
  venues = Venue.query.filter(func.lower(Venue.name).contains(search_term.lower())).all()
  for venue in venues:
    data.append({'id': venue.id, 'name': venue.name, 'num_upcoming_shows': venue.upcoming_shows})
  response['data'] = data
  response['count'] = len(venues)

  return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = Venue.query.filter_by(id=venue_id).first().__dict__
  past_shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).filter(Show.start_time < datetime.now()).filter(Venue.id == venue_id).all()
  upcoming_shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).filter(Show.start_time > datetime.now()).filter(Venue.id == venue_id).all()
  data['past_shows'] = [{'artist_id': a.id, 'artist_name': a.name, 'artist_image_link': a.image_link, 'start_time': str(s.start_time)} for (v, s, a) in past_shows]
  data['upcoming_shows'] = [{'artist_id': a.id, 'artist_name': a.name, 'artist_image_link': a.image_link, 'start_time': str(s.start_time)} for (v, s, a) in upcoming_shows]
  data['past_show_count'] = len(data['past_shows'])
  data['upcoming_show_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=data)


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue = request.form.to_dict()  # name, city, state, address, pone, genres, fb link  
  try:
    new_venue = Venue(name=venue['name'], city=venue['city'], state=venue['state'],
                      address=venue['address'], phone=venue['phone'], genres=request.form.getlist('genres'), 
                      facebook_link=venue['facebook_link'])
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')  # on success
  except Exception as e:
    db.session.rollback()
    flash('Venue ' + request.form['name'] + ' was not listed, please try again!')  # on fail
  finally:
    db.session.close()

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    ven = Venue.query.get(venue_id)
    db.session.delete(ven)
    db.session.commit()
    flash('Venue was successfully deleted!')  # on success
  except Exception as e:
    db.session.rollback()
    flash('Venue was not deleted, please try again!')  # on fail
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
  response = {}
  data = []
  artists = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower())).all()
  for artist in artists:
    data.append({'id': artist.id, 'name': artist.name, 'num_upcoming_shows': artist.upcoming_shows})
  response['data'] = data
  response['count'] = len(artists)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  data = Artist.query.filter_by(id=artist_id).first().__dict__
  past_shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).filter(Show.start_time < datetime.now()).filter(Artist.id == artist_id).all()
  upcoming_shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).filter(Show.start_time > datetime.now()).filter(Artist.id == artist_id).all()
  data['past_shows'] = [{'venue_id': v.id, 'venue_name': v.name, 'venue_image_link': v.image_link, 'start_time': str(s.start_time)} for (v, s, a) in past_shows]
  data['upcoming_shows'] = [{'venue_id': v.id, 'venue_name': v.name, 'venue_image_link': v.image_link, 'start_time': str(s.start_time)} for (v, s, a) in upcoming_shows]
  data['past_show_count'] = len(data['past_shows'])
  data['upcoming_show_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # get the info from the artist page
  form = ArtistForm()
  artist= Artist.query.filter_by(id=artist_id).all()[0]
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = request.form.to_dict()
  try:
    Artist.query.filter_by(id=artist_id).update(artist)
    Artist.query.filter_by(id=artist_id).update(dict(genres=request.form.getlist('genres')))
    db.session.commit()
    flash('Artist ' + artist['name'] + ' was successfully listed!')  # on success
  except Exception as e:
    db.session.rollback()
    flash('Artist ' + artist['name'] + ' was not listed, please try again!')  # on fail
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).all()[0]
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = request.form.to_dict()
  try:
    Venue.query.filter_by(id=venue_id).update(venue)
    Venue.query.filter_by(id=venue_id).update(dict(genres=request.form.getlist('genres')))
    db.session.commit()
    flash('Artist ' + venue['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('Artist ' + venue['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  artist = request.form.to_dict() 
  try:
    new_artist = Artist(name=artist['name'], city=artist['city'], state=artist['state'],
                        phone=artist['phone'], genres=request.form.getlist('genres'), 
                        facebook_link=artist['facebook_link'])
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + artist['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('Artist ' + artist['name'] + ' was not listed, please try again!')
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  --------------------------------- Artists Start -------------------------------


#  ------------------------------- Shows Start ---------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = db.session.query(Venue, Show, Artist).filter(Venue.id == Show.venue_id).filter(Artist.id == Show.artist_id).all()
  data = []
  
  for (v, s, a) in shows:
    data.append({
      'venue_id': v.id, 
      'venue_name': v.name, 
      'artist_id': a.id, 
      'artist_name': a.name, 
      'artist_image_link': a.image_link, 
      'start_time': str(s.start_time)
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # creates new show
  try:
    show = request.form.to_dict()
    start_time_format = datetime.strptime(show['start_time'], '%Y-%m-%d %H:%M:%S')
    new_show = Show(venue_id=show['venue_id'], artist_id=show['artist_id'], start_time=start_time_format)
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    app.logger.info(e)
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

#  ------------------------------- Debug Start ---------------------------------


#  -------------------------------  Start App ---------------------------------


# Default port:
if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0')
