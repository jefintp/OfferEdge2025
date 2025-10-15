from django.shortcuts import render, redirect
from .forms import QuoteForm
from quotes.models import Quote
from requirements.models import Requirement
from deals.models import Deal

# 🔍 Explore all posted requirements
def explore_requirements_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    user_id = request.session['userid']
    requirements = Requirement.objects(buyerid__ne=user_id)  # ✅ Exclude own requirements

    return render(request, 'quotes/explore_quotes.html', {
        'requirements': requirements
    })

# 📥 Place a quote on a specific requirement
def place_quote_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    requirement = Requirement.objects(id=reqid).first()
    if not requirement:
        return redirect('/quotes/explore')

    # ✅ Prevent self-bidding
    if requirement.buyerid == request.session['userid']:
        return render(request, 'quotes/place_quote.html', {
            'requirement': requirement,
            'form': None,
            'self_quote_blocked': True
        })

    # ✅ Prevent duplicate quote
    existing = Quote.objects(req_id=str(requirement.id), seller_id=request.session['userid']).first()
    if existing:
        print("⚠️ Duplicate quote detected")
        return redirect('/quotes/explore')

    if request.method == 'POST':
        form = QuoteForm(request.POST, request.FILES)
        if form.is_valid():
            quote = Quote(
                req_id=str(requirement.id),
                seller_id=request.session['userid'],
                price=form.cleaned_data['price'],
                deliveryTimeline=form.cleaned_data['deliveryTimeline'],
                notes=form.cleaned_data['notes']
            )
            if request.FILES.get('attachments'):
                quote.attachments.put(
                    request.FILES['attachments'],
                    content_type=request.FILES['attachments'].content_type
                )
            quote.save()
            return redirect('/quotes/explore')
    else:
        form = QuoteForm()

    return render(request, 'quotes/place_quote.html', {
        'form': form,
        'requirement': requirement,
        'self_quote_blocked': False
    })

# 📜 View all quotes placed by the logged-in seller
def my_quotes_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    seller_id = request.session['userid']
    my_quotes = Quote.objects(seller_id=seller_id).order_by('-createdon')

    # 🔍 Build a map: requirement_id → finalized quote_id
    finalized_map = {
        deal.requirement_id: deal.quote_id
        for deal in Deal.objects()
    }

    enriched_quotes = []
    for quote in my_quotes:
        requirement = Requirement.objects(id=quote.req_id).first()
        finalized_id = finalized_map.get(quote.req_id)

        # 🔹 Determine status
        if finalized_id == str(quote.id):
            status = "selected"
        elif finalized_id:
            status = "rejected"
        else:
            status = "in_progress"

        enriched_quotes.append({
            "quote": quote,
            "requirement": requirement,
            "status": status
        })

    return render(request, 'quotes/my_quotes.html', {
        'quote_data': enriched_quotes,
        'userid': seller_id
    })

# 📊 View all quotes for a specific requirement
def quotes_for_requirement_view(request, reqid):
    req = Requirement.objects(id=reqid).first()
    if not req:
        return redirect('/quotes/explore')

    quotes = Quote.objects(req_id=reqid).order_by('-createdon')

    # ✅ Detect finalized quote from Deal model
    finalized_quote_id = None
    for quote in quotes:
        deal = Deal.objects(quote_id=str(quote.id)).first()
        if deal:
            finalized_quote_id = str(deal.quote_id)
            break

    # ✅ Build chat eligibility map
    chat_flags = {}
    try:
        if req.negotiation_mode == "negotiation" and req.negotiation_trigger_price is not None:
            trigger_price = float(req.negotiation_trigger_price)
            for quote in quotes:
                if float(quote.price) < trigger_price:
                    chat_flags[str(quote.id)] = True
    except Exception as e:
        print(f"⚠️ Error checking chat eligibility for quotes in requirement {reqid}: {e}")

    # ✅ Build quote status map
    quote_status_map = {}
    for quote in quotes:
        qid = str(quote.id)
        if finalized_quote_id == qid:
            quote_status_map[qid] = "selected"
        elif finalized_quote_id:
            quote_status_map[qid] = "rejected"
        else:
            quote_status_map[qid] = "in_progress"

    userid = request.session.get("userid")

    return render(request, "quotes/quotes_for_requirement.html", {
        "requirement": req,
        "quotes": quotes,
        "finalized_quote_id": finalized_quote_id,
        "chat_flags": chat_flags,
        "quote_status_map": quote_status_map,
        "userid": userid
    })