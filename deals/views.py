from bson import ObjectId, errors
from django.shortcuts import redirect, render
from datetime import datetime
from deals.models import Deal
from quotes.models import Quote
from requirements.models import Requirement
from users.models import User

def finalize_quote_view(request, quote_id):
    if 'userid' not in request.session or request.method != 'POST':
        return redirect('/users/login')

    try:
        quote_obj_id = ObjectId(quote_id.strip())
    except errors.InvalidId:
        return redirect('/users/dashboard')

    quote = Quote.objects(id=quote_obj_id).first()
    if not quote:
        return redirect('/users/dashboard')

    if Deal.objects(quote_id=str(quote.id)).first():
        return redirect('/users/dashboard')

    try:
        req_obj_id = ObjectId(quote.req_id.strip())
    except errors.InvalidId:
        return redirect('/users/dashboard')

    req = Requirement.objects(id=req_obj_id).first()
    if not req:
        return redirect('/users/dashboard')

    seller = User.objects(userid=quote.seller_id).first()
    if not seller:
        return redirect('/users/dashboard')

    quote.finalized = True
    quote.save()

    req.finalized_quote_id = str(quote.id)
    req.save()

    deal = Deal(
        quote_id=str(quote.id),
        requirement_id=str(req.id),
        buyer_id=req.buyerid,
        seller_id=quote.seller_id,
        finalized_by=request.session['userid'],
        method="manual",
        finalized_on=datetime.now()
    )
    deal.save()

    request.session['finalized_success'] = True
    return redirect('/users/dashboard')
def deal_dashboard_view(request):
    deals = Deal.objects()
    deal_data = []

    for deal in deals:
        quote = Quote.objects(id=deal.quote_id).first()
        requirement = Requirement.objects(id=deal.requirement_id).first()
        seller = User.objects(username=deal.seller_id).first()
        buyer = User.objects(username=deal.buyer_id).first()

        deal_data.append({
            "deal": deal,
            "quote": quote,
            "requirement": requirement,
            "seller": seller,
            "buyer": buyer
        })

    return render(request, "deals/deal_dashboard.html", {"deal_data": deal_data})