from django.shortcuts import render, redirect
from .forms import QuoteForm
from .models import Quote
from requirements.models import Requirement

# 🔍 Explore all posted requirements
def explore_requirements_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    all_reqs = Requirement.objects().order_by('-createdAt')
    return render(request, 'quotes/explore_quotes.html', {'requirements': all_reqs})


# 📥 Place a quote on a specific requirement
def place_quote_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    requirement = Requirement.objects(id=reqid).first()
    if not requirement:
        return redirect('/quotes/explore')

    if request.method == 'POST':
        form = QuoteForm(request.POST, request.FILES)
        if form.is_valid():
            quote = Quote(
                req_id=str(requirement.id),  # ✅ Save as string to match Quote.req_id
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
        'requirement': requirement
    })


# 📜 View all quotes placed by the logged-in seller
def my_quotes_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    seller_id = request.session['userid']
    my_quotes = Quote.objects(seller_id=seller_id).order_by('-createdon')
    return render(request, 'quotes/my_quotes.html', {'quotes': my_quotes})


# 📊 View all quotes for a specific requirement
def quotes_for_requirement_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    requirement = Requirement.objects(id=reqid).first()
    if not requirement:
        return redirect('/dashboard')

    quotes = Quote.objects(req_id=reqid).order_by('-createdon')

    # 💬 Enable chat only for quotes below trigger price
    chat_enabled_map = {}
    if requirement.negotiation_mode == "negotiation" and hasattr(requirement, 'negotiation_trigger_price'):
        for quote in quotes:
            chat_enabled_map[str(quote.id)] = quote.price < requirement.negotiation_trigger_price

    return render(request, 'quotes/quotes_for_requirement.html', {
        'requirement': requirement,
        'quotes': quotes,
        'chat_enabled_map': chat_enabled_map
    })