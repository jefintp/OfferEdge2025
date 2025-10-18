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
    negotiation_mode = StringField(choices=["lowest_bid", "negotiation"], required=True)
    negotiation_trigger_price = FloatField()  # Only used if negotiation is enabled
    # attachment = models.FileField(upload_to='uploads/', blank=True, null=True)

    # Moderation flags
    flagged = BooleanField(default=False)
    flag_reason = StringField()

    meta = {
        'indexes': [
            'buyerid',
            '-createdAt',
            'flagged',
        ]
    }
