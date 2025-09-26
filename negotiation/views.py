from django.shortcuts import render

# Create your views here.
moderated_users = []
for user in raw_users:
    moderated_users.append({
        'userid': user.userid,
        'is_admin': user.is_admin,
        'is_banned': user.is_banned,
        'is_buyer': user.userid in buyer_ids,
        'is_seller': user.userid in seller_ids,
    })