from django.db import models

# Create your models here.
from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime

class ChatSession(Document):
    quote_id = StringField(required=True)
    buyer_id = StringField(required=True)
    seller_id = StringField(required=True)
    created_on = DateTimeField(default=datetime.now)

class ChatMessage(Document):
    session_id = ReferenceField(ChatSession, required=True)
    sender_id = StringField(required=True)
    message = StringField(required=True)
    timestamp = DateTimeField(default=datetime.now)
