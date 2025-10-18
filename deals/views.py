from bson import ObjectId, errors
from django.shortcuts import redirect, render
from datetime import datetime
from deals.models import Deal
from quotes.models import Quote
from requirements.models import Requirement
from users.models import User
from negotiation.models import ChatSession, ChatMessage


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
        seller = User.objects(userid=deal.seller_id).first()
        buyer = User.objects(userid=deal.buyer_id).first()

        deal_data.append({
            "deal": deal,
            "quote": quote,
            "requirement": requirement,
            "seller": seller,
            "buyer": buyer
        })

    return render(request, "deals/deal_dashboard.html", {"deal_data": deal_data})


def finalized_deals_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    userid = request.session['userid']

    # Fetch deals where current user is buyer or seller
    deals = Deal.objects.filter(__raw__={
        "$or": [
            {"buyer_id": userid},
            {"seller_id": userid},
        ]
    }).order_by('-finalized_on')

    # Build ID sets for batching
    quote_ids = [d.quote_id for d in deals]
    req_ids = [d.requirement_id for d in deals]

    quotes = {str(q.id): q for q in Quote.objects(id__in=quote_ids)} if quote_ids else {}
    reqs = {str(r.id): r for r in Requirement.objects(id__in=req_ids)} if req_ids else {}

    # Map quote_id -> ChatSession (if exists)
    sessions = {str(s.quote_id): s for s in ChatSession.objects.filter(__raw__={"quote_id": {"$in": quote_ids}})} if quote_ids else {}

    items = []
    for d in deals:
        quote = quotes.get(str(d.quote_id))
        requirement = reqs.get(str(d.requirement_id))
        if not quote or not requirement:
            continue
        counterparty = d.seller_id if userid == d.buyer_id else d.buyer_id
        role = 'buyer' if userid == d.buyer_id else 'seller'

        # Last message preview
        last_msg = None
        session = sessions.get(str(d.quote_id))
        if session:
            last = ChatMessage.objects(session_id=session).order_by('-timestamp').first()
            if last:
                last_msg = last.message

        items.append({
            "id": str(d.id),
            "requirement_title": getattr(requirement, 'title', 'Untitled Requirement'),
            "finalized_at": getattr(d, 'finalized_on', None),
            "amount": getattr(quote, 'price', None),
            "quote_id": str(quote.id),
            "counterparty": counterparty,
            "role": role,
            "requirement_id": str(requirement.id),
            "last_message": last_msg,
        })

    return render(request, 'deals/finalized.html', {
        'deals': items,
        'userid': userid,
    })
