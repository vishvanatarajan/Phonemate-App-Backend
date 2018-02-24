from flask import jsonify, request, make_response
import time

#Custom imports
from phonemate import app, db
from phonemate.models.users import Users
from phonemate.models.tokens import BlacklistToken
from instance.config import DEVELOPER_EMAIL, DEVELOPER_PASSWORD

@app.route("/")
def index():
    return "Invalid Endpoint"

@app.route("/users/register", methods=['POST'])
def registerNewUser():
    data = request.get_json()
    newUser = Users(email=data['email'], password=data['password'], first_name=data['first_name'], last_name=data['last_name'])
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

@app.route("/users/tokens/blacklist", methods=['POST'])
def blacklistAllUserTokens():
    data = request.get_json()
    if data['email']==DEVELOPER_EMAIL and data['password']==DEVELOPER_PASSWORD:
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