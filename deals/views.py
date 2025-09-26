from django.shortcuts import render, redirect
from deals.models import Deal, Quote  # ✅ Use only one Quote model
from requirements.models import Requirement
from datetime import datetime

def finalize_quote_view(request, quote_id):
    if 'userid' not in request.session:
        return redirect('/users/login')

    quote = Quote.objects(id=quote_id).first()
    if not quote:
        return redirect('/users/dashboard')

    quote.finalized = True
    quote.save()

    req = Requirement.objects(id=quote.req_id).first()
    if req:
        req.status = "finalized"
        req.save()

        Deal(  # ✅ Correct model name
            quote_id=str(quote.id),
            buyer_id=req.buyerid,
            seller_id=quote.seller_id,
            finalized_by=request.session['userid'],
            method="manual"
        ).save()

    request.session['finalized_success'] = True  # ✅ Success flag
    return redirect('/users/dashboard')

def deal_history_view(request):
    userid = request.session.get('userid')
    if not userid:
        return redirect('/users/login')

    deals = Deal.objects(buyer_id=userid).order_by('-finalized_on')
    quotes = {deal.quote_id: Quote.objects.get(id=deal.quote_id) for deal in deals}

    return render(request, 'deal_history.html', {
        'deals': deals,
        'quotes': quotes
    })