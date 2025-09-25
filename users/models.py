# users/models.py
from django.db import models

# No custom user model needed for now
from mongoengine import Document, StringField
import bcrypt
class User(Document):
    userid = StringField(required=True, unique=True)
    passwordHash = StringField(required=True)
    def set_password(self, raw_password):
        self.passwordHash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode(), self.passwordHash.encode())

