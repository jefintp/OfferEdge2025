from django.shortcuts import render, redirect
from users.models import User
from requirements.models import Requirement
from quotes.models import Quote
from users.decorators import admin_required
from django.views.decorators.http import require_POST
from deals.models import Deal
from moderation.models import Report
from datetime import datetime
from requirements.utils import delete_requirement_and_related
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

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

    # Reports (recent)
    reports = Report.objects().order_by('-created_at')[0:50]
    # Enrich reports with deal/requirement info
    report_rows = []
    for r in reports:
        deal = Deal.objects(id=r.deal_id).first()
        req = Requirement.objects(id=getattr(deal, 'requirement_id', None)).first() if deal else None
        report_rows.append({
            'id': str(r.id),
            'deal_id': r.deal_id,
            'reporter_id': r.reporter_id,
            'reported_id': r.reported_id,
            'created_at': r.created_at,
            'status': getattr(r, 'status', 'open'),
            'reason': getattr(r, 'reason', '')[:120],
            'requirement_title': getattr(req, 'title', '(unknown)'),
        })

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
        'report_rows': report_rows,
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

# User report creation (participants only)

def create_report_view(request, deal_id):
    if 'userid' not in request.session:
        return redirect('/users/login')
    user = request.session['userid']
    deal = Deal.objects(id=deal_id).first()
    if not deal:
        return redirect('finalized_deals')
    if user not in [deal.buyer_id, deal.seller_id]:
        return HttpResponseForbidden()

    # Determine reported user
    reported = deal.seller_id if user == deal.buyer_id else deal.buyer_id

    if request.method == 'POST':
        reason = (request.POST.get('reason') or '').strip()
        if not reason:
            return render(request, 'moderation/report_form.html', {
                'deal': deal, 'reported': reported, 'error': 'Please provide a reason.'
            })
        # Avoid duplicate identical open report by same reporter on same deal
        if Report.objects(deal_id=str(deal.id), reporter_id=user, status='open').first():
            return redirect('finalized_deals')
        Report(
            deal_id=str(deal.id),
            reporter_id=user,
            reported_id=reported,
            requirement_id=getattr(deal, 'requirement_id', None),
            quote_id=getattr(deal, 'quote_id', None),
            reason=reason,
            status='open'
        ).save()
        return redirect('finalized_deals')

    return render(request, 'moderation/report_form.html', {'deal': deal, 'reported': reported})

# Admin: report detail view
@admin_required
def report_detail_view(request, report_id):
    r = Report.objects(id=report_id).first()
    if not r:
        return redirect('moderation_dashboard')
    deal = Deal.objects(id=r.deal_id).first()
    req = Requirement.objects(id=getattr(deal, 'requirement_id', None)).first() if deal else None
    quote = Quote.objects(id=getattr(deal, 'quote_id', None)).first() if deal else None
    return render(request, 'moderation/report_detail.html', {
        'report': r,
        'deal': deal,
        'requirement': req,
        'quote': quote,
    })
