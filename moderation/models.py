from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class Report(Document):
    deal_id = StringField(required=True)         # deals.Deal.id as string
    reporter_id = StringField(required=True)     # userid of reporter
    reported_id = StringField(required=True)     # userid being reported
    requirement_id = StringField()               # optional: requirement.id
    quote_id = StringField()                     # optional: quote.id
    reason = StringField(required=True)
    status = StringField(default="open")        # open, resolved
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            '-created_at',
            'reporter_id',
            'reported_id',
            'deal_id',
            'status',
        ]
    }
