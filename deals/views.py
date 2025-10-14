from django.shortcuts import render, redirect
from deals.models import Deal, Quote  # ✅ Use only one Quote model
from requirements.models import Requirement
from datetime import datetime
def finalize_quote_view(request, quote_id):
    if 'userid' not in request.session:
        return redirect('/users/login')

    quote = Quote.objects(id=quote_id).first()
    if not quote or quote.finalized:
        return redirect('/users/dashboard')

    req = Requirement.objects(id=quote.req_id).first()
    if not req:
        return redirect('/users/dashboard')

    # ✅ Finalize quote
    quote.finalized = True
    quote.save()

    # ✅ Mark requirement as finalized
    req.finalized_quote_id = str(quote.id)
    req.save()

    # ✅ Create deal
    Deal(
        quote_id=str(quote.id),
        buyer_id=req.buyerid,
        seller_id=quote.seller_id,
        finalized_by=request.session['userid'],
        method="manual",
        finalized_on=datetime.now()
    ).save()

    # ✅ Flash success flag
    request.session['finalized_success'] = True
    return redirect('/users/dashboard')