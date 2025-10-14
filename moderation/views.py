from django.shortcuts import render, redirect
from users.models import User
from requirements.models import Requirement
from quotes.models import Quote
from users.decorators import admin_required
from django.views.decorators.csrf import csrf_exempt

@admin_required
def moderation_dashboard(request):
    # Fetch all users
    raw_users = User.objects().order_by('-id')

    # Fetch requirements
    requirements = Requirement.objects().only(
        'buyerid', 'title', 'description', 'createdAt'
    ).order_by('-createdAt')

    # Fetch quotes
    quotes = Quote.objects().only(
        'req_id', 'seller_id', 'price', 'finalized', 'createdon'
    ).order_by('-createdon')

    # Build buyer/seller role flags
    buyer_ids = set(req.buyerid for req in requirements)
    seller_ids = set(q.seller_id for q in quotes)

    # Build moderated user list
    moderated_users = []
    for user in raw_users:
        moderated_users.append({
            'userid': user.userid,
            'is_admin': user.is_admin,
            'is_banned': user.is_banned,
            'is_buyer': user.userid in buyer_ids,
            'is_seller': user.userid in seller_ids,
        })

    return render(request, 'moderation/moderation_panel.html', {
        'users': moderated_users,
        'requirements': requirements,
        'quotes': quotes
    })

# 🔧 Moderation Actions

@admin_required
@csrf_exempt
def ban_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user:
        user.is_banned = True
        user.save()
    return redirect('moderation_dashboard')

@admin_required
@csrf_exempt
def unban_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user:
        user.is_banned = False
        user.save()
    return redirect('moderation_dashboard')

@admin_required
@csrf_exempt
def delete_user_view(request, user_id):
    user = User.objects(userid=user_id).first()
    if user:
        user.delete()
    return redirect('moderation_dashboard')

@admin_required
@csrf_exempt
def finalize_quote_view(request, quote_id):
    quote = Quote.objects(id=quote_id).first()
    if quote:
        quote.finalized = True
        quote.save()
    return redirect('moderation_dashboard')

@admin_required
@csrf_exempt
def delete_quote_view(request, quote_id):
    quote = Quote.objects(id=quote_id).first()
    if quote:
        quote.delete()
    return redirect('moderation_dashboard')