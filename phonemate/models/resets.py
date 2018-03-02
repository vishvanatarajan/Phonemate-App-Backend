import datetime
from mongoengine import Document, URLField, DateTimeField, ObjectIdField

from phonemate import app

class ResetPassword(Document):
    user_id = ObjectIdField(required=True)
    reset_link = URLField()
    requested_at = DateTimeField(required=True, null=False)
    expires_at = DateTimeField(required=True, null=False)

    meta = {"collection":"reset_password"}

    def clean(self):
        self.reset_link = str(self.reset_link)
        self.requested_at = datetime.datetime.now()
        self.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=15)

    @staticmethod
    def get_request_from_url(url):
        return ResetPassword.objects(reset_link=url).first()