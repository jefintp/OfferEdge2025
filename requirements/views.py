from django.shortcuts import render, redirect
from .forms import RequirementForm
from .models import Requirement
from datetime import datetime
from django.views.decorators.http import require_POST
from requirements.utils import delete_requirement_and_related
from quotes.models import Quote
from django.conf import settings
import os
import uuid


def post_requirement_view(request):
    if 'userid' not in request.session:
        return redirect('/users/login')

    if request.method == 'POST':
        form = RequirementForm(request.POST, request.FILES)  # ✅ Include request.FILES

        # Idempotency: validate nonce to prevent double submission
        posted_nonce = request.POST.get('nonce')
        session_nonce = request.session.get('req_form_nonce')
        if not posted_nonce or posted_nonce != session_nonce:
            return redirect('/users/dashboard')

        if form.is_valid():
            # Extra safety: avoid duplicates by checking recent similar requirement
            existing = Requirement.objects(
                buyerid=request.session['userid'],
                title=form.cleaned_data['title'],
                deadline=form.cleaned_data['deadline']
            ).first()
            if existing:
                # Consume nonce to avoid repeats
                request.session.pop('req_form_nonce', None)
                return redirect('/users/dashboard')

            req = Requirement(
                buyerid=request.session['userid'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                quantity=form.cleaned_data['quantity'],
                expectedPriceRange=form.cleaned_data['expectedPriceRange'],
                deadline=form.cleaned_data['deadline'],
                category=form.cleaned_data['category'],
                location=form.cleaned_data['location'],
                negotiation_mode=form.cleaned_data['negotiation_mode']
            )
            if req.negotiation_mode == "negotiation":
                req.negotiation_trigger_price = form.cleaned_data['negotiation_trigger_price']

            # ✅ Save uploaded file if present
            uploaded_file = request.FILES.get('attachment')
            if uploaded_file:
                try:
                    folder = os.path.join(settings.MEDIA_ROOT, 'requirement_uploads')
                    os.makedirs(folder, exist_ok=True)
                    safe_name = f"{uuid.uuid4()}_{uploaded_file.name}"
                    path = os.path.join(folder, safe_name)
                    with open(path, 'wb+') as dest:
                        for chunk in uploaded_file.chunks():
                            dest.write(chunk)
                    req.attachment_url = f"/media/requirement_uploads/{safe_name}"
                    req.attachment_type = getattr(uploaded_file, 'content_type', None)
                    req.attachment_name = uploaded_file.name
                except Exception:
                    # If upload fails, continue without attachment
                    pass

            req.save()
            # Consume nonce after successful save
            request.session.pop('req_form_nonce', None)
            return redirect('/users/dashboard')
    else:
        form = RequirementForm()
        # Issue a fresh nonce for this form render
        request.session['req_form_nonce'] = str(uuid.uuid4())

    return render(request, 'requirements/post_requirement.html', {'form': form, 'nonce': request.session.get('req_form_nonce')})

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



