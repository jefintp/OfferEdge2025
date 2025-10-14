from mongoengine import Document, StringField, IntField, DateTimeField, FloatField, BooleanField
from datetime import datetime

class Requirement(Document):
    title = StringField(required=True)
    description = StringField()
    quantity = IntField()
    expectedPriceRange = StringField()
    deadline = DateTimeField()
    createdAt = DateTimeField(default=datetime.utcnow)
    buyerid = StringField(required=True)
    negotiation_mode = StringField(choices=["negotiation", "fixed"])
    negotiation_trigger_price = FloatField()

class Quote(Document):
    req_id = StringField(required=True)  # links to Requirement.id
    seller_id = StringField(required=True)
    price = FloatField(required=True)
    deliveryTimeline = StringField(required=True)
    notes = StringField()
    createdon = DateTimeField(default=datetime.utcnow)
    finalized = BooleanField(default=False)
    attachments = StringField()  # Placeholder for file storage reference

class Deal(Document):
    quote_id = StringField(required=True)
    buyer_id = StringField(required=True)
    seller_id = StringField(required=True)
    finalized_on = DateTimeField(default=datetime.utcnow)
    finalized_by = StringField()  # usually buyer
    method = StringField(choices=["auto", "manual"])
    status = StringField(default="finalized")  # or "cancelled"