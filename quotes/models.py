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

    # Attachment metadata (saved under MEDIA_ROOT/quote_uploads)
    attachment_url = StringField()       # e.g. "/media/quote_uploads/uuid_filename.pdf"
    attachment_type = StringField()      # e.g. "image/png", "application/pdf"
    attachment_name = StringField()      # original filename

    createdon = DateTimeField(default=datetime.utcnow)
    finalized = BooleanField(default=False)
