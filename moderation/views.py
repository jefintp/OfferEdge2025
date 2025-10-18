from django.shortcuts import render, redirect
from users.models import User
from requirements.models import Requirement
from quotes.models import Quote
from users.decorators import admin_required
from django.views.decorators.http import require_POST
from deals.models import Deal
from datetime import datetime
from requirements.utils import delete_requirement_and_related

@admin_required
def moderation_dashboard(request):
    # Filters and pagination
    q = request.GET.get('q', '').strip()
    page = max(int(request.GET.get('page', 1) or 1), 1)
    page_size = 20
    skip = (page - 1) * page_size

    # Users
    user_qs = User.objects()
    if q:
        user_qs = user_qs(userid__icontains=q)
    # Hide users until a search is performed
    raw_users = []
    if q:
        raw_users = user_qs.order_by('-id')[skip: skip + page_size]

    # Requirements
    req_qs = Requirement.objects().only('buyerid', 'title', 'description', 'createdAt', 'flagged', 'flag_reason')
    if q:
        req_qs = req_qs(title__icontains=q)
    requirements = req_qs.order_by('-createdAt')[0: page_size]

    # Quotes
    quote_qs = Quote.objects().only('req_id', 'seller_id', 'price', 'finalized', 'createdon')
    quotes = quote_qs.order_by('-createdon')[0: page_size]

    # Buyer/Seller flags
    buyer_ids = set(req.buyerid for req in requirements)
    seller_ids = set(qo.seller_id for qo in quotes)

    moderated_users = []
    for user in raw_users:
        moderated_users.append({
            'userid': user.userid,
            'is_admin': user.is_admin,
            'is_banned': user.is_banned,
            'is_buyer': user.userid in buyer_ids,
            'is_seller': user.userid in seller_ids,
        })

    # Annotate quotes with requirement title
    req_map = {str(r.id): r.title for r in Requirement.objects(id__in=list(set(q.req_id for q in quotes)))} if quotes else {}
    quote_rows = []
    for qo in quotes:
        quote_rows.append({
            'id': str(qo.id),
            'req_title': req_map.get(qo.req_id, '(untitled)'),
            'seller_id': qo.seller_id,
            'price': qo.price,
            'finalized': qo.finalized,
            'createdon': qo.createdon,
        })

    return render(request, 'moderation/moderation_panel.html', {
        'users': moderated_users,
        'requirements': requirements,
        'quote_rows': quote_rows,
        'q': q,
        'page': page,
    })

# 🔧 Moderation Actions

@admin_required
@require_POST
def ban_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user and not user.is_admin and user.userid != 'admin':
        user.is_banned = True
        user.save()
    return redirect('moderation_dashboard')

@admin_required
@require_POST
def unban_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user and not user.is_admin and user.userid != 'admin':
        user.is_banned = False
        user.save()
    return redirect('moderation_dashboard')

@admin_required
@require_POST
def delete_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user and not user.is_admin and user.userid != 'admin':
        user.delete()
    return redirect('moderation_dashboard')

@admin_required
@require_POST
def finalize_quote_view(request, quote_id):
    quote = Quote.objects(id=quote_id).first()
    if not quote:
        return redirect('moderation_dashboard')
    req = Requirement.objects(id=quote.req_id).first()
    if not req:
        return redirect('moderation_dashboard')

    # If a deal already exists, do nothing
    if Deal.objects(quote_id=str(quote.id)).first():
        return redirect('moderation_dashboard')

    quote.finalized = True
    quote.save()

    req.finalized_quote_id = str(quote.id)
    req.save()

    Deal(
        quote_id=str(quote.id),
        requirement_id=str(req.id),
        buyer_id=req.buyerid,
        seller_id=quote.seller_id,
        finalized_by=request.session.get('userid', 'admin'),
        method="manual",
        finalized_on=datetime.now(),
    ).save()

    return redirect('moderation_dashboard')

@admin_required
@require_POST
def delete_quote_view(request, quote_id):
    quote = Quote.objects(id=quote_id).first()
    if quote:
        quote.delete()
    return redirect('moderation_dashboard')


@admin_required
@require_POST
def delete_requirement_mod_view(request, req_id):
    # Admin-triggered cascade delete (requirement + related quotes + deals)
    ok, msg = delete_requirement_and_related(req_id=req_id, user_id=request.session.get('userid'), is_admin=True)
    return redirect('moderation_dashboard')
