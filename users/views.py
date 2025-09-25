from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import User
import bcrypt
from requirements.models import Requirement
from quotes.models import Quote
from bson import ObjectId

# ✅ Registration
def signup_view(request):
    if request.method == 'POST':
        userid = request.POST['userid']
        password = request.POST['password']
        if User.objects(userid=userid).first():
            return render(request, 'register.html', {'error': 'User already exists'})
        user = User(userid=userid)
        user.set_password(password)
        user.save()
        request.session['userid'] = userid
        return redirect('/dashboard')
    return render(request, 'register.html')

# ✅ Login
def login_view(request):
    if request.method == 'POST':
        userid = request.POST['userid']
        password = request.POST['password']
        user = User.objects(userid=userid).first()
        if user and user.check_password(password):
            request.session['userid'] = userid
            return redirect('/dashboard')
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# ✅ Logout
def logout_view(request):
    request.session.flush()
    return redirect('/users/login')

# ✅ Dashboard (protected manually)
def dashboard_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    userid = request.session['userid']

    # 🔹 Requirements you posted
    raw_requirements = Requirement.objects(buyerid=userid).order_by('-createdAt')
    my_requirements = []

    for req in raw_requirements:
        quotes = list(Quote.objects(req_id=str(req.id)))
        chat_flags = {}

        if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
            for quote in quotes:
                if quote.price < req.negotiation_trigger_price:
                    chat_flags[str(quote.id)] = True

        my_requirements.append({
            'id': str(req.id),
            'title': req.title,
            'description': req.description,
            'quantity': req.quantity,
            'expectedPriceRange': req.expectedPriceRange,
            'deadline': req.deadline,
            'createdAt': req.createdAt,
            'quotes': quotes,
            'chat_flags': chat_flags
        })

    # 🔹 Quotes you placed
    my_quotes = Quote.objects(seller_id=userid).order_by('-createdon')

    # 🔹 Requirement title map
    req_map = {str(req.id): req.title for req in Requirement.objects()}

    # 💬 Chat eligibility map (for placed quotes)
    chat_enabled_map = {}

    for quote in my_quotes:
        req = Requirement.objects(id=quote.req_id).first()
        if req and getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
            if quote.price < req.negotiation_trigger_price:
                chat_enabled_map[str(quote.id)] = True

    return render(request, 'dashboard.html', {
        'userid': userid,
        'requirements': my_requirements,
        'my_quotes': my_quotes,
        'req_map': req_map,
        'chat_enabled_map': chat_enabled_map
    })

# ✅ Test MongoDB Save
def test_user_save(request):
    User(userid="jefin123", passwordHash="hashed_pw_abc123").save()
    return HttpResponse("User saved to MongoDB!")

# ✅ Debug view for quotes
def debug_quotes_view(request):
    userid = request.session.get('userid')
    reqs = Requirement.objects(buyerid=userid)
    data = []

    for req in reqs:
        quotes = Quote.objects(req_id=str(req.id))
        data.append({
            'req_id': str(req.id),
            'title': req.title,
            'quote_count': quotes.count(),
            'quotes': [
                {
                    'price': q.price,
                    'delivery': q.deliveryTimeline,
                    'notes': q.notes,
                    'quote_id': str(q.id),
                    'seller': q.seller_id
                } for q in quotes
            ]
        })

    return JsonResponse({'requirements': data})