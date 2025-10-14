from django.db import models

# Create your models here.
from mongoengine import Document, StringField, FloatField, DateTimeField, FileField,BooleanField
from datetime import datetime

class Quote(Document):
    req_id = StringField(required=True)               # Requirement ID
    seller_id = StringField(required=True)            # Seller ID
    price = FloatField(required=True)                 # Quoted price
    deliveryTimeline = StringField(required=True)     # Delivery timeline
    notes = StringField()                             # Optional message
    attachments = FileField()                         # Optional file
    createdon = DateTimeField(default=datetime.utcnow)
    finalized = BooleanField(default=False)