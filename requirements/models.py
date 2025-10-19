from django.db import models

# Create your models here.
from mongoengine import Document, StringField, IntField, DateTimeField, FloatField, BooleanField
from datetime import datetime

class Requirement(Document):
    buyerid = StringField(required=True)
    title = StringField(required=True)
    description = StringField(required=True)
    quantity = IntField(required=True)
    expectedPriceRange = StringField(required=True)
    deadline = DateTimeField(required=True)
    createdAt = DateTimeField(default=datetime.utcnow)

    # New fields
    category = StringField(choices=["service", "product"])  # "service" or "product"
    location = StringField()  # free-text location/city/area

    negotiation_mode = StringField(choices=["lowest_bid", "negotiation"], required=True)
    negotiation_trigger_price = FloatField()  # Only used if negotiation is enabled

    # Attachment metadata (saved under MEDIA_ROOT/requirement_uploads)
    attachment_url = StringField()       # e.g. "/media/requirement_uploads/uuid_filename.pdf"
    attachment_type = StringField()      # e.g. "image/png", "application/pdf"
    attachment_name = StringField()      # original filename

    # Moderation flags
    flagged = BooleanField(default=False)
    flag_reason = StringField()

    meta = {
        'indexes': [
            'buyerid',
            '-createdAt',
            'flagged',
            'category',
            'location',
        ]
    }
