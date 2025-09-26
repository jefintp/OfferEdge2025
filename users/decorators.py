# users/decorators.py
from functools import wraps
from django.shortcuts import redirect
from users.models import User

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        userid = request.session.get('userid')
        user = User.objects(userid=userid).first()
        if not user or not user.is_admin:
            request.session['next'] = request.path  # ✅ Save intended path
            return redirect('/users/login')
        return view_func(request, *args, **kwargs)
    return wrapper