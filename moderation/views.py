from django.shortcuts import render, redirect
from users.models import User
from requirements.models import Requirement
from users.decorators import admin_required


from requirements.models import Requirement
from quotes.models import Quote

@admin_required
def moderation_dashboard(request):
    raw_users = User.objects().order_by('-id')
    requirements = Requirement.objects().only('buyerid', 'title', 'description', 'createdAt').order_by('-createdAt')
    quotes = Quote.objects().only('seller_id')

    buyer_ids = set(req.buyerid for req in requirements)
    seller_ids = set(q.seller_id for q in quotes)

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
        'users':    moderated_users,
        'requirements': requirements
    })