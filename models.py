from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate


app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#-------------------------------------- Models Start --------------------------------------#

class Venue(db.Model):
  __tablename__ = 'Venue'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  genres = db.Column(db.ARRAY(db.String(200)))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))
  website = db.Column(db.String(120))
  show = db.relationship('Show', backref='venue', lazy=True)

  def upcoming_shows():
    shows = db.session.query(Venue.id, Venue.name).join(Show)\
      .filter(Show.start_time > datetime.now).count()

  def past_shows():
    shows = db.session.query(Venue.id, Venue.name).join(Show)\
      .filter(Show.start_time < datetime.now).count()


  def __repr__(self):
    return f'<id: {self.id}, name: {self.name}, state: {self.state}>'

class Artist(db.Model):
  __tablename__ = 'Artist'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.ARRAY(db.String(200)))
  seeking_venue = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))
  website = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  show = db.relationship('Show', backref='artist', lazy=True)

  def __repr__(self):
    return f'<id: {self.id}, name: {self.name}, state: {self.city}>'

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
  start_time = db.Column(db.DateTime)

  def __repr__(self):
    return f'<id: {self.id}, venue_id: {self.venue_id},\
       artist_id: {self.artist_id}, time: {self.start_time}>'

#-------------------------------------- Models End --------------------------------------#

