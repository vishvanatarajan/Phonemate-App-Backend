from flask import Flask
from flask_mongoengine import MongoEngine
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail

from pymongo import MongoClient

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
#Create a PyMongo db object to read scraped data from CSV file and store it into MongoDB database
pyMongoClient = MongoClient('mongodb://localhost:27017/')
pyMongoDB = pyMongoClient[DATABASE_NAME]
#Initialize app with Bcrypt module to securely store passwords
bcrypt = Bcrypt(app)
#Instance of Mail class inititalized with our app
mail = Mail(app)

from phonemate import views