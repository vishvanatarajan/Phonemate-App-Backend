from flask import Flask
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_cors import CORS

#Custom imports
from instance.config import DATABASE_NAME, DATABASE_URI

app = Flask(__name__, instance_relative_config = True)
app.config.from_pyfile('config.py')
app.config['MONGODB_SETTINGS'] = {
    'db': DATABASE_NAME,
    'host': DATABASE_URI
}

#Enable CORS so that the Android app can access the API using Retrofit
CORS(app)
#Create database object to manipulate database using models and MongoEngine ORM
db = MongoEngine(app)
#Initialize app with Bcrypt module to securely store passwords
bcrypt = Bcrypt(app)

from phonemate import views