import os
import uuid
import time
import datetime
import json
import pandas as pd
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
        return make_response(jsonify(responseObject)), 403
    else:
        try:
            newUser.save()
            responseObject = {
                'status': 'success',
                'message': 'Successfully registered',
                'userid': str(newUser.id)
            }
            return make_response(jsonify(responseObject)), 201
        except Exception as exception:
            print(str(exception))
            responseObject = {
                'status': 'failure',
                'message': 'Internal Server Error: Please try again later'
            }
            return make_response(jsonify(responseObject)), 500

@app.route("/users/login", methods=['POST'])
def authenticateUser():
    data = request.get_json()
    user = Users.get_user_from_email(data['email'])
    if user is None:
        responseObject = {
            'status': 'failure', 
            'message': 'User does not exist. Please register first'
        }
        return make_response(jsonify(responseObject)), 403
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
                return make_response(jsonify(responseObject)), 500
        else:
            responseObject = {
                'status': 'failure',
                'message': 'Incorrect username or password'
            }
            return make_response(jsonify(responseObject)), 404

@app.route("/users/login/google", methods=['POST'])
def userGoogleSignIn():
    user_token = request.headers['Authorization']
    data = request.get_json()
    try:
        id_info = id_token.verify_oauth2_token(user_token, requests.Request(), GOOGLE_CLIENT_ID)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
        user_id = id_info['sub']
        new_user = Users(_id=user_id, email=data['email'], password=uuid.uuid4().hex, first_name=data['first_name'],
                         last_name=data['last_name'], google_sign_in=True)
        new_user.save()
        auth_token = new_user.encode_auth_token(user_id)
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
        return make_response(jsonify(responseObject)), 403

@app.route("/users/google/logout", methods=['POST'])
def removeGoogleUser():
    user_token = request.headers['Authorization']
    try:
        id_info = id_token.verify_oauth2_token(user_token, requests.Request(), GOOGLE_CLIENT_ID)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
        user_id = id_info['sub']
        user = Users.objects(_id=user_id).first()
        if isinstance(user, Users):
            Users.objects(_id=user_id).delete()
            responseObject = {
                'status': 'success',
                'message': 'Google account has been removed from our app server'
            }
            return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'status': 'failure',
                'message': 'Google account has not been linked with the PhoneMate app'
            }
            return make_response(jsonify(responseObject)), 401
    except ValueError:
        print("Invalid Token encountered during Google Sign out")
        responseObject = {
            'status': 'failure',
            'message': 'Invalid client ID'
        }
        return make_response(jsonify(responseObject)), 403

@app.route("/users/profile", methods=['GET'])
def getUserProfile():
    user = Users.get_user_from_token(request.headers['Authorization'])
    if isinstance(user, Users):
        responseObject = {
            'status': 'success',
            'userid': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'registered_on': user.registered_on
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'status': 'failure',
            'message': user
        }
        return make_response(jsonify(responseObject)), 401

@app.route("/users/logout", methods=['POST'])
def userLogout():
    user_id = Users.get_id_from_token(request.headers['Authorization'])
    if user_id == 'Signature expired. Please log in again.' or user_id == 'Invalid token. Please log in again.' or user_id == 'Token blacklisted. Please log in again.':
        responseObject = {
            'status': 'failure',
            'message': user_id
        }
        return make_response(jsonify(responseObject)), 401
    elif user_id == 'Bearer token is malformed. Please try again with valid token':
        responseObject = {
            'status': 'failure',
            'message': user_id
        }
        return make_response(jsonify(responseObject)), 400
    else:
        try:
            auth_token = request.headers['Authorization'].split(" ")[1]
            blacklist_token = BlacklistToken(token=auth_token)
            blacklist_token.save()
            responseObject = {
                'status': 'success',
                'message': 'Successfully logged out.'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as exception:
            print(str(exception))
            responseObject = {
                'status': 'failure',
                'message': 'Internal Server Error. Please try again later'
            }
            return make_response(jsonify(responseObject)), 500

@app.route("/users/forgot/password", methods=['POST'])
def userForgotPassword():
    data = request.get_json()
    user = Users.get_user_from_email(data['email'])
    if user is None:
        responseObject = {
            'status': 'failure', 
            'message': 'User does not exist. Please register first'
        }
        return make_response(jsonify(responseObject)), 403
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
            return render_template('fpwd-404-not-found.html'), 404
    else:
        responseObject = {
            'status': 'failure',
            'message': 'Invalid URL'
        }
        return make_response(jsonify(responseObject)), 400

@app.route("/users/password/reset", methods=['PUT'])
def resetPassword():
    user_id = request.form['user_id']
    new_password = request.form['password']
    user = Users.get_user_from_id(user_id)
    if user is None:
        return render_template('password-reset.html', action_result="true", action_msg="Could not reset password. Please try again from the app."), 401
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
        return make_response(jsonify(responseObject)), 403

#Run the scrape.py file in the web-scarping folder before calling this function
@app.route("/phones/scraped/insert", methods=['POST'])
def insertIntoDBFromCSV():
    data = request.get_json()
    if data['email'] == MAIL_USERNAME and data['password'] == MAIL_PASSWORD:
        phones_collection = pyMongoDB.phones
        directory_path = os.path.dirname(__file__)
        csv_file_path = os.path.join(directory_path, 'static/phone-data.csv')
        csv_data = pd.read_csv(csv_file_path)
        csv_data.drop(csv_data.columns[[0]], axis=1, inplace=True)
        for i in range(len(csv_data['Cost'])):
            try:
                csv_data['Cost'][i] = csv_data['Cost'][i][1:]
            except Exception as exception:
                pass
        output_file_path = os.path.join(directory_path, 'static/phones.csv')
        csv_data.to_csv(output_file_path)
        phones_csv = pd.read_csv(output_file_path)
        json_data = json.loads(phones_csv.to_json(orient='records'))
        phones_collection.remove()
        phones_collection.insert(json_data)
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
        return make_response(jsonify(responseObject)), 403

@app.route("/phones/featured", methods=['GET'])
def featuredPhones():
    phones = ["iPhone X", "Pixel 2", "Redmi Note 5", "Samsung Galaxy S8", "Nokia 8"]
    result = []
    for phone in phones:
        regex = ".*"+phone+".*"
        result.append(pyMongoDB.phones.find_one( { "Name": { "$regex": regex } }, { '_id': False } ))
    return make_response(jsonify(result)), 200