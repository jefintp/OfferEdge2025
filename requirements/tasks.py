from requirements.models import Requirement
from quotes.models import Quote
import datetime

def auto_select_lowest_bids():
    now = datetime.datetime.utcnow()
    expired = Requirement.objects(deadline__lte=now, negotiation_mode="lowest_bid", selected_quote_id=None)

    for req in expired:
        quotes = Quote.objects(req_id=req.id)
        if quotes:
            selected = min(quotes, key=lambda q: q.price)
            req.selected_quote_id = selected.id
            req.save()