import os
import uuid
import time
import datetime
import re
import json
import pprint
import pandas as pd
import numpy as np
from random import choice
from string import ascii_uppercase
from flask import jsonify, request, make_response, render_template
from flask_mail import Mail, Message
from google.oauth2 import id_token
from google.auth.transport import requests

#Custom imports
from phonemate import app, db, mail, pyMongoDB
from phonemate.models.users import Users
from phonemate.models.tokens import BlacklistToken
from phonemate.models.resets import ResetPassword
from instance.config import MAIL_USERNAME, MAIL_PASSWORD, SERVER_URL, GOOGLE_CLIENT_ID

@app.route("/")
def index():
    return "Invalid Endpoint"

@app.route("/users/register", methods=['POST'])
def registerNewUser():
    data = request.get_json()
    newUser = Users(email=data['email'], password=data['password'], first_name=data['first_name'], last_name=data['last_name'],                                google_sign_in=False)
    if newUser.exists() == True:
        responseObject = {
                'status': 'failure',
                'message': 'User already exists. Please log in'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        try:
            newUser.save()
            responseObject = {
                'status': 'success',
                'message': 'Successfully registered',
                'userid': str(newUser.id)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as exception:
            print(str(exception))
            responseObject = {
                'status': 'failure',
                'message': 'Internal Server Error: Please try again later'
            }
            return make_response(jsonify(responseObject)), 200

@app.route("/users/login", methods=['POST'])
def authenticateUser():
    data = request.get_json()
    user = Users.get_user_from_email(data['email'])
    if user is None:
        responseObject = {
            'status': 'failure', 
            'message': 'User does not exist. Please register first'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        if user.validate_user_by_pwd(data['password']) == True:
            try:
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    responseObject = {
                        'status': 'success',
                        'message': 'Login successful',
                        'token': 'Bearer ' + auth_token.decode()
                    }
                    return make_response(jsonify(responseObject)), 200
            except Exception as exception:
                print(str(exception))
                responseObject = {
                    'status': 'failure',
                    'message': 'Internal Server Error: Please try again later'
                }
                return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'status': 'failure',
                'message': 'Incorrect username or password'
            }
            return make_response(jsonify(responseObject)), 200

@app.route("/users/login/google", methods=['POST'])
def userGoogleSignIn():
    user_token = request.headers['Authorization']
    data = request.get_json()
    try:
        id_info = id_token.verify_oauth2_token(user_token, requests.Request(), GOOGLE_CLIENT_ID)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
        new_user = Users(email=data['email'], password=uuid.uuid4().hex, first_name=data['first_name'],
                         last_name=data['last_name'], google_sign_in=True)
        new_user.save()
        auth_token = new_user.encode_auth_token(new_user.id)
        if auth_token:
            responseObject = {
                'status': 'success',
                'message': 'Login successful',
                'token': 'Bearer ' + auth_token.decode()
            }
            return make_response(jsonify(responseObject)), 200
    except ValueError:
        print("Invalid Token encountered during Google Sign in")
        responseObject = {
            'status': 'failure',
            'message': 'Invalid client ID. Please use a valid Google account to login'
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/users/profile", methods=['POST'])
def getUserProfile():
    user = Users.get_user_from_token(request.headers['Authorization'])
    if isinstance(user, Users):
        responseObject = {
            'status': 'success',
            'userid': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'city': user.city,
            'phone': user.phone,
            'registered_on': user.registered_on,
            'message': 'User profile sent successfully'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'status': 'failure',
            'message': user
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/users/profile/update", methods=['PUT'])
def updateUserProfile():
    user = Users.get_user_from_token(request.headers['Authorization'])
    if isinstance(user, Users):
        data = request.get_json()
        user.update(set__first_name = str(data['first_name']), set__last_name = str(data['last_name']), set__city = str(data['city']),                     set__phone = str(data['phone']))
        responseObject = {
            'status': 'success',
            'message': 'Profile has been updated successfully'
        }
    else:
        responseObject = {
            'status': 'failure',
            'message': 'Invalid token. Please log in again'
        }
    return make_response(jsonify(responseObject)), 200

@app.route("/users/forgot/password", methods=['PUT'])
def userForgotPassword():
    data = request.get_json()
    user = Users.get_user_from_email(data['email'])
    if user is None:
        responseObject = {
            'status': 'failure', 
            'message': 'User does not exist. Please register first'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        url = str(SERVER_URL) + str("/users/password/") + ''.join(choice(ascii_uppercase) for _ in range(12)) + str(user.id)
        reset = ResetPassword(user_id=user.id, reset_link=url)
        reset.save()
        msg = Message("Password reset request for your PhoneMate account", sender="services@phonemate.com", recipients=[user.email])
        msg.html = render_template('fpwd-otp-email.html', action_name=user.first_name, action_url=str(url))
        mail.send(msg)
        responseObject = {
            'status': 'success',
            'message': 'An email with the steps to reset the password has been sent to the registered email id.',
            'request_id': str(reset.id)
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/users/password/<link>", methods=['GET'])
def resetPasswordLink(link):
    url = str(SERVER_URL) + str("/users/password/") + str(link)
    reset_request = ResetPassword.get_request_from_url(url)
    if reset_request is not None:
        if reset_request.expires_at > datetime.datetime.now():
            return render_template('password-reset.html', action_id=reset_request.user_id, action_result="false"), 200
        else:
            return render_template('fpwd-404-not-found.html'), 200
    else:
        responseObject = {
            'status': 'failure',
            'message': 'Invalid URL'
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/users/password/reset", methods=['PUT'])
def resetPassword():
    user_id = request.form['user_id']
    new_password = request.form['password']
    user = Users.get_user_from_id(user_id)
    if user is None:
        return render_template('password-reset.html', action_result="true", action_msg="Could not reset password. Please try again from the app."), 200
    else:
        user.update_user_pwd(new_password)
        return render_template('password-reset.html', action_result="true", action_msg="Password has been reset successfully!"), 200
    
@app.route("/users/tokens/blacklist", methods=['POST'])
def blacklistAllUserTokens():
    data = request.get_json()
    if data['email'] == MAIL_USERNAME and data['password'] == MAIL_PASSWORD:
        BlacklistToken.blacklistAllTokens()
        responseObject = {
            'status': 'success',
            'message': 'Tokens have been blacklisted successfully.'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'status': 'failure',
            'message': 'Authentication Failure'
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/users/recommendation", methods=['POST'])
def recommendedPhones():
    data = request.get_json()
    collection = pyMongoDB.smart_phones
    temp_collection = pyMongoDB.temp_collection
    temp_collection.drop()
    result = []
    smartphone = int(data['smartphone'])
    busage = int(data['busage'])
    price = int(data['price'])
    os = int(data['os'])
    storage = int(data['storage'])
    battery = int(data['battery'])
    camera = int(data['camera'])
    screen = int(data['screen'])
    ram = int(data['ram'])
    weight = int(data['weight'])
    result.clear()
    if smartphone == -1 or busage == -1 or price == -1 or os == -1 or storage == -1 or battery == -1 or camera == -1 or screen == -1 or ram == -1 or weight == -1:
        responseObject = {
            'status': 'failure',
            'message': 'No requirements were specified.'
        }
        result.append(responseObject)
        return make_response(jsonify(result)), 201
    else:
        min_storage = 0
        max_storage = 0
        min_battery = 0
        max_battery = 0
        min_camera = 0
        max_camera = 0
        min_screen = 0
        max_screen = 0
        min_ram = 0
        max_ram = 0
        min_weight = 0
        max_weight = 0
        regex = ""
        if os == 1:
            regex = ".*Android.*"
        elif os == 2:
            regex = ".*iOS.*"
        elif os == 3:
            regex = ".*iOS.*|.*Android.*"
        else:
            regex = "^((?!android|ios).)*$"
        if storage == 0:
            max_storage = 8
        elif storage == 1:
            min_storage = 8
            max_storage = 32
        else:
            min_storage = 32
            max_storage = 1024
        if battery == 0:
            max_battery = 2000
        elif battery == 1:
            min_battery = 2000
            max_battery = 3500
        else:
            min_battery = 3500
            max_battery = 15000
        if camera == 0:
            max_camera = 4
        elif camera == 1:
            min_camera = 4
            max_camera = 10
        else:
            min_camera = 10
            max_camera = 1024
        if screen == 0:
            min_screen = 0
            max_screen = 3.5
        elif screen == 1:
            min_screen = 3.5
            max_screen = 5
        else:
            min_screen = 5
            max_screen = 50
        if ram == 0:
            max_ram = 1.5
        elif ram == 1:
            min_ram = 1.5
            max_ram = 3
        else:
            min_ram = 3
            max_ram = 100
        if weight == 0:
            max_weight = 115
        else:
            max_weight = 1000
        if smartphone == 0:
            collection = pyMongoDB.feature_phones
        if busage == 0:
            for phone in collection.find({'Cost': {'$lte': price}, 'Primary Camera': {'$gte': 12}, 'Battery Capacity': {'$gte': 3000}, 'Operating System': {'$regex':regex, '$options':'i'}}, {'_id':0}):
                result.append(phone)
            if len(result) > 6:
                for phone in result:
                    temp_collection.insert(phone)
                result.clear()
                for phone in temp_collection.find({'Internal Storage': {'$gte': min_storage, '$lte': max_storage}}, {'_id':0}).sort('Primary Camera', -1).limit(10):
                    result.append(phone)
                if len(result) < 2:
                    for phone in collection.find({'Cost': {'$lte': price}, 'Primary Camera': {'$gte': 12}, 'Battery Capacity': {'$gte': 3000}, 'Operating System': {'$regex':regex, '$options':'i'}}, {'_id':0}):
                        result.append(phone)
            else:
                for phone in collection.find({'Cost': {'$lte': price}, 'Operating System': {'$regex': regex, '$options':'i'}}, {'_id':0}).sort('Primary Camera', -1).limit(10):
                    result.append(phone)
        elif busage == 1:
            for phone in collection.find({'Cost': {'$lte':price}, 'Operating System': {'$regex':regex, '$options':'i'}, 'Primary Camera': {'$gte':min_camera, '$lte':max_camera}, 'Battery Capacity': {'$gte':min_battery, '$lte':max_battery}}, {'_id':0}).limit(10):
                result.append(phone)
            if len(result) > 2:
                for phone in result:
                    temp_collection.insert(phone)
                result.clear()
                for phone in temp_collection.find({'Internal Storage': {'$gte':min_storage, '$lte':max_storage}, 'RAM': {'$gte':min_ram, '$lte':max_ram}, 'Display size':{'$gte':min_screen, '$lte':max_screen}, 'Weight':{'$gte':min_weight, '$lte':max_weight}}, {'_id':0}).limit(10):
                    result.append(phone)
                if len(result) < 2:
                    result.clear()
                    for phone in collection.find({'Cost': {'$lte':price}, 'Operating System': {'$regex':regex, '$options':'i'}, 'Primary Camera': {'$gte':min_camera, '$lte':max_camera}, 'Battery Capacity': {'$gte':min_battery, '$lte':max_battery}}, {'_id':0}).limit(10):
                        result.append(phone)
            else:
                for phone in collection.find({'Cost':{'$lte':price}, 'Operating System': {'$regex':regex, '$options':'i'}}, {'_id':0}).sort('Cost', 1).limit(10):
                    result.append(phone)
        elif busage == 2:
            for phone in collection.find({'Cost':{'$lte':price}, 'Battery':{'$gte':min_battery, '$lte':max_battery}, 'Operating System':{'$regex':regex, '$options':'i'}}, {'_id':0}):
                result.append(phone)
            if len(result)>10:
                for phone in result:
                    temp_collection.insert(phone)
                result.clear()
                for phone in temp_collection.find({'Internal Storage': {'$gte':min_storage, '$lte':max_storage}, 'RAM':{'$gte':min_ram, '$lte':max_ram}, 'Primary Camera':{'$gte':min_camera, '$lte':max_camera}}, {'_id':0}):
                    result.append(phone)
                if len(result) < 2:
                    result.clear()
                    for phone in collection.find({'Cost':{'$lte':price}, 'Battery':{'$gte':min_battery, '$lte':max_battery}, 'Operating System':{'$regex':regex, '$options':'i'}}, {'_id':0}):
                        result.append(phone)
            else:
                for phone in collection.find({'Cost':{'$lte':price}, 'Operating System':{'$regex':regex, '$options':'i'}}, {'_id':0}).sort('Cost', 1).limit(10):
                    result.append(phone)
        print(len(result))
        if(len(result)<1):
            result.clear()
            responseObject = {
                # 'status': 'Failure',
                # 'message': 'Could not find any items that match your requirements. Please change your requirements'
                
            }
            result.append(None)
        else:
            for phone in result:
                phone['Cost'] = str(phone['Cost'])
                if phone['Primary Camera'] == 0:
                    phone['Primary Camera'] = str("-")
                else:
                    phone['Primary Camera'] = str(phone['Primary Camera']) + " MP"
                if phone['Battery Capacity'] == 0:
                    phone['Battery Capacity'] = str("-")
                else:
                    phone['Battery Capacity'] = str(phone['Battery Capacity']) + " mAH"
                if phone['Internal Storage'] == 0:
                    phone['Internal Storage'] = str("-")
                else:
                    value = phone['Internal Storage']
                    if value > 0 and value < 1:
                        value = value * 1024
                        value = str(value) + " MB"
                    else:
                        value = str(value) + " GB"
                    phone['Internal Storage'] = value
                if phone['RAM'] == 0:
                    phone['RAM'] = str("-")
                else:
                    value = phone['RAM']
                    if value > 0 and value < 1:
                        value = value * 1024
                        value = str(value) + " MB"
                    else:
                        value = str(value) + " GB"
                    phone['RAM'] = value
                if phone['Display Size'] == 0:
                    phone['Display Size'] = str("-")
                else:
                    phone['Display Size'] = str(phone['Display Size']) + " inch"
                if phone['Weight'] == 0:
                    phone['Weight'] = str("-")
                else:
                    phone['Weight'] = str(phone['Weight']) + " g"
        return make_response(jsonify(result)), 200    

#Run the scrape.py file in the web-scarping folder before calling this function
@app.route("/phones/insert", methods=['POST'])
def insertIntoDBFromCSV():
    data = request.get_json()
    if data['email'] == MAIL_USERNAME and data['password'] == MAIL_PASSWORD:
        phones_collection = pyMongoDB.phones
        smartphones_collection = pyMongoDB.smart_phones
        featurephones_collection = pyMongoDB.feature_phones
        phones_collection.drop()
        smartphones_collection.drop()
        featurephones_collection.drop()
        directory_path = os.path.dirname(__file__)
        csv_file_path = os.path.join(directory_path, 'static/phones.csv')
        df = pd.read_csv(csv_file_path)
        df = df.replace(np.nan, '', regex=True)
        regex = re.compile(r"MP.*")
        batregex = re.compile(r" .*")
        convertregex = re.compile(r" MB")
        storageregex = re.compile(r"[ GB|$$GB]")
        displayregex = re.compile(r" inch")
        weightregex = re.compile(r" g")
        for i in range(len(df)):
            df['Cost'][i] = float(df['Cost'][i].replace(",",""))
            camera = df['Primary Camera'][i]
            if camera is "":
                camera = 0
            else:
                camera = regex.sub("", camera)
            df['Primary Camera'][i] = float(camera)
            battery = df['Battery Capacity'][i]
            if battery is "":
                battery = 0
            else:
                battery = batregex.sub("", battery)
            df['Battery Capacity'][i] = float(battery)
            storage = df['Internal Storage'][i]
            if "NA" in storage:
                storage = 0
            elif "MB" in storage:
                storage = convertregex.sub("", storage)
                storage = float(storage)/1024
            elif "GB" in storage:
                storage = storageregex.sub("", storage)
                storage = float(storage)
            else:
                storage = 0
            df['Internal Storage'][i] = storage
            ram = df['RAM'][i]
            if "MB" in ram:
                ram = convertregex.sub("", ram)
                ram = float(ram)/1024
            elif "GB" in ram:
                ram = storageregex.sub("", ram)
                ram = float(ram)
            else:
                ram = 0
            df['RAM'][i] = ram
            display = df['Display Size'][i]
            if display is "":
                display = 0
            else:
                display = displayregex.sub("", display)
            df['Display Size'][i] = float(display)
            weight = df['Weight'][i]
            if weight is "":
                weight = 0
            else:
                weight = weightregex.sub("", weight)
            df['Weight'][i] = float(weight)
        smartPhoneDF = pd.DataFrame()
        featurePhoneDF = pd.DataFrame()
        smartPhoneDF, featurePhoneDF = [x for _, x in df.groupby(df['Browse Type'] != 'Smartphones')]
        phones_json_data = json.loads(df.to_json(orient='records'))
        smartphone_json_data = json.loads(smartPhoneDF.to_json(orient='records'))
        featurephone_json_data = json.loads(featurePhoneDF.to_json(orient='records'))
        phones_collection.insert(phones_json_data)
        smartphones_collection.insert(smartphone_json_data)
        featurephones_collection.insert(featurephone_json_data)
        responseObject = {
            'status': 'success',
            'message': 'Phones imported successfully from CSV file.'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'status': 'failure',
            'message': 'Authentication Failure'
        }
        return make_response(jsonify(responseObject)), 200

@app.route("/phones/featured", methods=['GET'])
def featuredPhones():
    phones = ["iPhone X", "Pixel 2", "Redmi Note 5", "Samsung Galaxy S8", "Nokia 8"]
    result = []
    for phone in phones:
        regex = ".*"+phone+".*"
        result.append(pyMongoDB.phones.find_one( { "Name": { "$regex": regex } }, { '_id': 0 } ))
    return make_response(jsonify(result)), 200

@app.route("/phones/new", methods=['GET'])
def newPhones():
    phones = ["Moto Z2 Play", "Moto X4", "VIVO V7+", "Moto G5", "Honor Holly 3"]
    result = []
    for phone in phones:
        regex = ".*"+phone+".*"
        result.append(pyMongoDB.phones.find_one( { "Name": { "$regex": regex } }, { '_id': 0 } ))
    return make_response(jsonify(result)), 200

@app.route("/phones/top5", methods=['GET'])
def top5Phones():
    phones = ["Redmi Note 4", "iPhone 8", "Nokia 5", "HTC U11", "LG G6"]
    result = []
    for phone in phones:
        regex = ".*"+phone+".*"
        result.append(pyMongoDB.phones.find_one( { "Name": { "$regex": regex } }, { '_id': 0 } ))
    return make_response(jsonify(result)), 200