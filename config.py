import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database - done


# TODO IMPLEMENT DATABASE URL - done
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:despicable01@localhost:5432/musicapp'

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:despicable01@localhost:5432/fyyurapp'
SQLALCHEMY_TRACK_MODIFICATIONS = False
