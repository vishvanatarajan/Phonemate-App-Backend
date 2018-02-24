import datetime
import os
from mongoengine import Document, StringField, DateTimeField

#Custom imports
from instance.config import SECRET_KEY
from phonemate import app

class BlacklistToken(Document):
    token = StringField(required=True)
    blacklisted_on = DateTimeField(required=True, null=False)

    meta = {"collection":"blacklisted_tokens"}

    def clean(self):
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id:  token: {}'.format(self.token)

    # Unadvisable hack used. Not recommended for use in production environment
    @staticmethod
    def blacklistAllTokens():
        app.config['SECRET_KEY'] = os.urandom(24)

    @staticmethod
    def checkBlacklist(auth_token):
        result = BlacklistToken.objects(token=auth_token).first()
        if result:
            return True
        return False
            
