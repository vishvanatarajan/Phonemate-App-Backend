import datetime
import jwt
from mongoengine import Document, BooleanField, IntField, EmailField, StringField, DateTimeField, ValidationError

#Custom imports
from phonemate import bcrypt, app
from phonemate.models.tokens import BlacklistToken
from instance.config import BCRYPT_LOG_ROUNDS

class Users(Document):
    email = EmailField(required = True, allow_utf8_user=True)
    password = StringField(min_length = 6, required = True)
    first_name = StringField(min_length = 3)
    last_name = StringField(min_length = 2)
    registered_on = DateTimeField(null=False, required=True)

    def clean(self):
        self.email = str(self.email)
        self.password = bcrypt.generate_password_hash(self.password, BCRYPT_LOG_ROUNDS).decode('utf-8')
        self.first_name = str(self.first_name)
        self.last_name = str(self.last_name)
        self.registered_on = datetime.datetime.now()

    def exists(self):
        existing_user = Users.objects(email=self.email).first()
        if existing_user is None:
            return False
        return True

    def validate_user_by_pwd(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def update_user_pwd(self, new_password):
        new_password = bcrypt.generate_password_hash(new_password, BCRYPT_LOG_ROUNDS).decode('utf-8')
        self.update(password=new_password)

    def encode_auth_token(self, user_id):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365),
                'iat': datetime.datetime.utcnow(),
                'sub': str(user_id)
            }
            return jwt.encode(
                payload,
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as exception:
            return exception

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(
                auth_token,
                app.config['SECRET_KEY']
            )
            is_blacklisted_token = BlacklistToken.checkBlacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'
    
    @staticmethod
    def get_id_from_token(auth_header):
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                return 'Bearer token is malformed.'
        else:
            auth_token = ''
        jwtdecoded = Users.decode_auth_token(auth_token)
        return jwtdecoded
                
    @staticmethod
    def get_user_from_email(email):
        return Users.objects(email=email).first()

    @staticmethod
    def get_user_from_token(auth_header):
        user_id = Users.get_id_from_token(auth_header)
        if user_id == 'Signature expired. Please log in again.' or user_id == 'Invalid token. Please log in again.' or user_id == 'Token blacklisted. Please log in again.':
            user = user_id
        elif user_id == 'Bearer token is malformed. Please try again with valid token':
            user = user_id
        else:
            user = Users.objects(id=user_id).first()
        return user

    @staticmethod
    def get_user_from_id(user_id):
        return Users.objects(id=user_id).first()