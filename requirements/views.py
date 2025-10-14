from django.shortcuts import render, redirect
from .forms import RequirementForm
from .models import Requirement
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

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




@csrf_exempt  # Remove once CSRF is fully wired
def delete_requirement_view(request, reqid):
    if 'userid' not in request.session:
        return redirect('/users/login')

    # Debug: print session flags
    print("Session userid:", request.session.get('userid'))
    print("Session is_admin:", request.session.get('is_admin'))

    # Ensure admin-only access
    if not bool(request.session.get('is_admin')):  # robust check
        return redirect('/moderation/')  # fallback to moderation, not dashboard

    # Delete the requirement
    Requirement.objects(id=reqid).delete()
    return redirect('/moderation/')
    print("Request method:", request.method)
    print("Deleting reqid:", reqid)
    print("Found:", Requirement.objects(id=reqid).first())



