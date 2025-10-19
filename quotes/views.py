from django.shortcuts import render, redirect
from .forms import QuoteForm
from quotes.models import Quote
from requirements.models import Requirement
from deals.models import Deal
from negotiation.models import ChatSession
from django.views.decorators.http import require_POST
from django.conf import settings
import os
import uuid

# 🔍 Explore all posted requirements
def explore_requirements_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    user_id = request.session['userid']

    # Filters
    category = (request.GET.get('category') or '').strip().lower()
    location = (request.GET.get('location') or '').strip()
    q = (request.GET.get('q') or '').strip()

    qs = Requirement.objects(buyerid__ne=user_id)

    # Exclude requirements already quoted by this seller; show them again only if the quote is deleted
    quoted_req_ids = list({qobj.req_id for qobj in Quote.objects(seller_id=user_id).only('req_id')})
    if quoted_req_ids:
        qs = qs(id__nin=quoted_req_ids)

    if category in ('service', 'product'):
        qs = qs(category=category)
    if location:
        # stored normalized to lowercase; compare case-insensitively
        qs = qs(location=location.casefold())
    if q:
        qs = qs(title__icontains=q)

    requirements = qs.order_by('-createdAt')

    context = {
        'requirements': requirements,
        'filter_category': category,
        'filter_location': location,
        'filter_q': q,
    }

    # If HTMX request, return only the list partial
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'quotes/partials/explore_list.html', context)

    return render(request, 'quotes/explore_quotes.html', context)

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
            # Save uploaded file if present
            uploaded = request.FILES.get('attachments')
            if uploaded:
                try:
                    folder = os.path.join(settings.MEDIA_ROOT, 'quote_uploads')
                    os.makedirs(folder, exist_ok=True)
                    safe_name = f"{uuid.uuid4()}_{uploaded.name}"
                    path = os.path.join(folder, safe_name)
                    with open(path, 'wb+') as dest:
                        for chunk in uploaded.chunks():
                            dest.write(chunk)
                    quote.attachment_url = f"/media/quote_uploads/{safe_name}"
                    quote.attachment_type = getattr(uploaded, 'content_type', None)
                    quote.attachment_name = uploaded.name
                except Exception:
                    pass
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
    userid = request.session.get("userid")

    # If a finalized quote exists, restrict chat to the finalized quote only
    if finalized_quote_id:
        for quote in quotes:
            qid = str(quote.id)
            if qid == finalized_quote_id:
                chat_flags[qid] = True  # buyer and the finalized seller will be allowed by start_chat_view
            else:
                chat_flags[qid] = False
    else:
        # Buyer can start negotiation on any quote (when not finalized)
        if userid and req and userid == req.buyerid:
            for quote in quotes:
                chat_flags[str(quote.id)] = True

        # Sellers under trigger price remain eligible
        try:
            if req.negotiation_mode == "negotiation" and req.negotiation_trigger_price is not None:
                trigger_price = float(req.negotiation_trigger_price)
                for quote in quotes:
                    if float(quote.price) < trigger_price:
                        chat_flags[str(quote.id)] = True
        except Exception as e:
            print(f"⚠️ Error checking chat eligibility for quotes in requirement {reqid}: {e}")

        # If a chat session already exists for a quote, allow access regardless
        try:
            for quote in quotes:
                if ChatSession.objects(quote_id=str(quote.id)).first():
                    chat_flags[str(quote.id)] = True
        except Exception:
            pass

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


@require_POST
def delete_quote_view(request, quote_id):
    if 'userid' not in request.session:
        return redirect('/users/login')

    user = request.session.get('userid')
    is_admin = bool(request.session.get('is_admin'))

    quote = Quote.objects(id=quote_id).first()
    if not quote:
        return redirect('/users/dashboard')

    # Allow only owner or admin to delete
    if not is_admin and quote.seller_id != user:
        return redirect('/users/dashboard')

    # Block deletion if this quote is accepted/finalized
    if getattr(quote, 'finalized', False):
        return redirect('/users/dashboard')

    # Block deletion if a deal exists for this quote
    deal = Deal.objects(quote_id=str(quote.id)).first()
    if deal:
        return redirect('/users/dashboard')

    quote.delete()
    return redirect('/users/dashboard')
