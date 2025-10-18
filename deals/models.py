from datetime import datetime
from mongoengine import Document, StringField, IntField, DateTimeField, FloatField, BooleanField, ReferenceField
from quotes.models import Quote
from requirements.models import Requirement
from users.models import User

class Requirement(Document):
    title = StringField(required=True)
    description = StringField()
    quantity = IntField()
    expectedPriceRange = StringField()
    deadline = DateTimeField()
    createdAt = DateTimeField(default=datetime.utcnow)
    buyerid = StringField(required=True)  # stores buyer username
    negotiation_mode = StringField(choices=["negotiation", "fixed"])
    negotiation_trigger_price = FloatField()

class Quote(Document):
    req_id = StringField(required=True)  # stores Requirement.id as string
    seller_id = StringField(required=True)  # stores seller username
    price = FloatField(required=True)
    deliveryTimeline = StringField(required=True)
    notes = StringField()
    createdon = DateTimeField(default=datetime.utcnow)
    finalized = BooleanField(default=False)
    attachments = StringField()  # placeholder for file storage reference

class Deal(Document):
    quote_id = StringField(required=True)
    requirement_id = StringField(required=True)
    buyer_id = StringField(required=True)
    seller_id = StringField(required=True)
    finalized_on = DateTimeField(default=datetime.utcnow)
    finalized_by = StringField()
    method = StringField(choices=["auto", "manual"])
    status = StringField(default="finalized")

    meta = {
        'indexes': [
            'buyer_id',
            'seller_id',
            '-finalized_on',
        ]
    }
