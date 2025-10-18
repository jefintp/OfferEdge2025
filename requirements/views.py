from django.shortcuts import render, redirect
from .forms import RequirementForm
from .models import Requirement
from datetime import datetime
from django.views.decorators.http import require_POST
from requirements.utils import delete_requirement_and_related
from quotes.models import Quote


def post_requirement_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    if request.method == 'POST':
        form = RequirementForm(request.POST, request.FILES)  # ✅ Include request.FILES
        if form.is_valid():
            req = Requirement(
                buyerid=request.session['userid'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                quantity=form.cleaned_data['quantity'],
                expectedPriceRange=form.cleaned_data['expectedPriceRange'],
                deadline=form.cleaned_data['deadline'],
                negotiation_mode=form.cleaned_data['negotiation_mode']
            )
            if req.negotiation_mode == "negotiation":
                req.negotiation_trigger_price = form.cleaned_data['negotiation_trigger_price']

            # ✅ Save uploaded file if present
            uploaded_file = request.FILES.get('attachment')
            if uploaded_file:
                req.attachment = uploaded_file

            req.save()
            return redirect('/users/dashboard')
    else:
        form = RequirementForm()

    return render(request, 'requirements/post_requirement.html', {'form': form})

def my_requirements_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    reqs = Requirement.objects(buyerid=request.session['userid']).order_by('-createdAt')
    return render(request, 'requirements/my_requirements.html', {'requirements': reqs})


def requirement_detail_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    req = Requirement.objects(id=reqid).first()
    if not req:
        return redirect('/users/dashboard')

    quotes = Quote.objects(req_id=str(req.id)).order_by('-createdon')
    quotes_count = quotes.count()

    can_delete = request.session.get('userid') == req.buyerid or bool(request.session.get('is_admin'))

    return render(request, 'requirements/detail.html', {
        'requirement': req,
        'quotes': quotes,
        'quotes_count': quotes_count,
        'can_delete': can_delete,
    })




@require_POST
def delete_requirement_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    userid = request.session.get('userid')
    is_admin = bool(request.session.get('is_admin'))

    ok, msg = delete_requirement_and_related(req_id=reqid, user_id=userid, is_admin=is_admin)
    # Optionally, you could set a flash message here via session
    return redirect('/users/dashboard')



