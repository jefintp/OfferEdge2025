from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import User
import bcrypt
from requirements.models import Requirement
from quotes.models import Quote
from deals.models import Deal  # ✅ Fix: import Deal model
from bson import ObjectId
from datetime import datetime

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

            # ✅ Force boolean conversion for MongoEngine field
            raw_admin_flag = user.is_admin
            request.session['is_admin'] = str(raw_admin_flag).lower() == 'true'

            # ✅ Debug prints to confirm
            print("User is_admin from DB:", raw_admin_flag)
            print("Session is_admin set to:", request.session['is_admin'])

            next_url = request.session.pop('next', None)
            return redirect(next_url or '/dashboard')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('/users/login')

# def dashboard_view(request):
#     if 'userid' not in request.session:
#         return redirect('/users/login')

#     userid = request.session['userid']

#     # 🔹 Requirements you posted
#     raw_requirements = Requirement.objects(buyerid=userid).order_by('-createdAt')
#     my_requirements = []
#     finalized_quote_map = {}

#     for req in raw_requirements:
#         quotes = list(Quote.objects(req_id=str(req.id)))
#         chat_flags = {}
#         finalized_quote_id = None

#         # 🔍 Check if any quote is finalized for this requirement
#         for quote in quotes:
#             deal = Deal.objects(quote_id=str(quote.id)).first()
#             if deal:
#                 finalized_quote_id = str(deal.quote_id)
#                 break

#         # ✅ Auto-finalize if deadline passed and negotiation is disabled
#         if not finalized_quote_id and req.deadline < datetime.now() and getattr(req, 'negotiation_mode', None) != "negotiation":
#             sorted_quotes = sorted(quotes, key=lambda q: float(q.price))
#             if sorted_quotes:
#                 best_quote = sorted_quotes[0]
#                 best_quote.finalized = True
#                 best_quote.save()

#                 seller = User.objects(id=best_quote.seller_id).first()

#                 Deal(
#                     quote_id=str(best_quote.id),
#                     buyer_id=req.buyerid,
#                     seller_id=best_quote.seller_id,
#                     finalized_by="system",
#                     method="auto",
#                     finalized_on=datetime.now(),
#                     quote=best_quote,
#                     requirement=req,
#                     seller=seller
#                 ).save()

#                 finalized_quote_id = str(best_quote.id)
#                 request.session['finalized_success'] = True

#         # 💬 Chat eligibility
#         if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
#             try:
#                 trigger_price = float(req.negotiation_trigger_price)
#                 for quote in quotes:
#                     if float(quote.price) < trigger_price:
#                         chat_flags[str(quote.id)] = True
#             except Exception as e:
#                 print(f"⚠️ Error comparing prices for {req.title}: {e}")

#         finalized_quote_map[str(req.id)] = finalized_quote_id

#         my_requirements.append({
#             'id': str(req.id),
#             'title': req.title,
#             'description': req.description,
#             'quantity': req.quantity,
#             'expectedPriceRange': req.expectedPriceRange,
#             'deadline': req.deadline,
#             'createdAt': req.createdAt,
#             'buyerid': req.buyerid,
#             'quotes': quotes,
#             'chat_flags': chat_flags
#         })

#     # 🔹 Quotes you placed
#     my_quotes = Quote.objects(seller_id=userid).order_by('-createdon')

#     # 🔹 Map requirement titles for placed quotes
#     req_map = {str(req.id): req.title for req in Requirement.objects()}

#     # 🔹 Chat eligibility for placed quotes
#     chat_enabled_map = {}
#     for quote in my_quotes:
#         try:
#             req = Requirement.objects.get(id=quote.req_id)
#             if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
#                 trigger_price = float(req.negotiation_trigger_price)
#                 if float(quote.price) < trigger_price:
#                     chat_enabled_map[str(quote.id)] = True
#         except Exception as e:
#             print(f"⚠️ Error checking chat eligibility for quote {quote.id}: {e}")

#     # ✅ Success banner logic
#     finalized_success = False
#     if request.session.get('finalized_success'):
#         finalized_success = True
#         del request.session['finalized_success']

#     return render(request, 'dashboard.html', {
#         'userid': userid,
#         'requirements': my_requirements,
#         'my_quotes': my_quotes,
#         'req_map': req_map,
#         'chat_enabled_map': chat_enabled_map,
#         'finalized_success': finalized_success,
#         'finalized_quote_map': finalized_quote_map
#     })



from datetime import datetime
from django.shortcuts import render, redirect
from deals.models import Deal
from quotes.models import Quote
from requirements.models import Requirement
from users.models import User


def dashboard_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    userid = request.session['userid']

    # 🔹 Buyer-side: posted requirements
    raw_requirements = Requirement.objects(buyerid=userid).order_by('-createdAt')
    my_requirements = []
    finalized_quote_map = {}

    for req in raw_requirements:
        req_id_str = str(req.id)
        quotes = list(Quote.objects(req_id=req_id_str))
        chat_flags = {}
        finalized_quote_id = None

        # 🔍 Check for finalized quote
        deal = Deal.objects(requirement_id=req_id_str).first()
        if deal:
            finalized_quote_id = str(deal.quote_id)

        # ✅ Auto-finalize if deadline passed and negotiation is disabled
        if not finalized_quote_id and req.deadline < datetime.now() and getattr(req, 'negotiation_mode', None) != "negotiation":
            sorted_quotes = sorted(quotes, key=lambda q: float(q.price))
            if sorted_quotes:
                best_quote = sorted_quotes[0]
                best_quote.finalized = True
                best_quote.save()

                Deal(
                    quote_id=str(best_quote.id),
                    requirement_id=req_id_str,
                    buyer_id=req.buyerid,
                    seller_id=best_quote.seller_id,
                    finalized_by="system",
                    method="auto",
                    finalized_on=datetime.now()
                ).save()

                finalized_quote_id = str(best_quote.id)
                request.session['finalized_success'] = True

        # ✅ Annotate quotes and select one for display
        selected_quote = None
        for quote in quotes:
            quote_id_str = str(quote.id)
            if quote_id_str == finalized_quote_id:
              selected_quote = quote

        if not selected_quote and quotes:
            selected_quote = quotes[0]

        # 💬 Chat eligibility
        if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
            try:
                trigger_price = float(req.negotiation_trigger_price)
                for quote in quotes:
                    if float(quote.price) < trigger_price:
                        chat_flags[str(quote.id)] = True
            except Exception as e:
                print(f"⚠️ Error comparing prices for {req.title}: {e}")

        finalized_quote_map[req_id_str] = finalized_quote_id

        my_requirements.append({
            'id': req_id_str,
            'title': req.title,
            'description': req.description,
            'quantity': req.quantity,
            'expectedPriceRange': req.expectedPriceRange,
            'deadline': req.deadline,
            'createdAt': req.createdAt,
            'buyerid': req.buyerid,
            'quotes': quotes,
            'selected_quote': selected_quote,
            'selected_quote_finalized': str(selected_quote.id) == finalized_quote_id if selected_quote else False,
            'chat_flags': chat_flags
        })

    # 🔹 Seller-side: placed quotes
    my_quotes = Quote.objects(seller_id=userid).order_by('-createdon')
    req_map = {str(req.id): req.title for req in Requirement.objects()}

    # 💬 Chat eligibility for placed quotes
    chat_enabled_map = {}
    for quote in my_quotes:
        try:
            req = Requirement.objects.get(id=quote.req_id)
            if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
                trigger_price = float(req.negotiation_trigger_price)
                if float(quote.price) < trigger_price:
                    chat_enabled_map[str(quote.id)] = True
        except Exception as e:
            print(f"⚠️ Error checking chat eligibility for quote {quote.id}: {e}")

    # ✅ Fallback: build finalized_quote_map from quotes if buyer-side is empty
    for deal in Deal.objects():
        req_id_str = deal.requirement_id
        finalized_quote_map[req_id_str] = str(deal.quote_id)

    # 🔹 Build quote_data for clean rendering
    quote_data = []
    for quote in my_quotes:
        quote_id_str = str(quote.id)
        req_id_str = quote.req_id
        req_title = req_map.get(req_id_str, "Untitled Requirement")
        status = "in_progress"

        finalized_id = finalized_quote_map.get(req_id_str)
        quote_id_str = str(quote.id)

        if finalized_id:
            if quote_id_str == finalized_id:
                status = "selected"
            else:
                status = "rejected"
        else:
            status = "in_progress"

        quote_data.append({
            "quote": quote,
            "requirement_title": req_title,
            "status": status
        })

    # ✅ Finalization banner
    finalized_success = False
    if request.session.get('finalized_success'):
        finalized_success = True
        del request.session['finalized_success']

    return render(request, 'dashboard.html', {
        'userid': userid,
        'requirements': my_requirements,
        'my_quotes': my_quotes,
        'req_map': req_map,
        'chat_enabled_map': chat_enabled_map,
        'finalized_success': finalized_success,
        'finalized_quote_map': finalized_quote_map,
        'quote_data': quote_data
    })