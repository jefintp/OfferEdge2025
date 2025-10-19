from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from negotiation.models import ChatSession, ChatMessage
from quotes.models import Quote
from requirements.models import Requirement
from deals.models import Deal
from datetime import datetime
from bson import ObjectId
import os
import uuid

def start_chat_view(request, quote_id):
    userid = request.session.get("userid")
    quote = Quote.objects(id=quote_id).first()
    if not quote or not userid:
        return redirect("/users/login")

    req = Requirement.objects(id=quote.req_id).first()
    if not req:
        return redirect("/users/dashboard")

    session = ChatSession.objects(quote_id=str(quote.id)).first()

    # If a deal is finalized for this requirement, only allow the finalized quote's participants
    deal = Deal.objects(requirement_id=str(req.id)).first()
    if deal and str(deal.quote_id) != str(quote.id):
        return redirect("/users/dashboard")

    # Buyer may always start or open
    if userid == req.buyerid:
        if not session:
            session = ChatSession(
                quote_id=str(quote.id),
                buyer_id=req.buyerid,
                seller_id=quote.seller_id
            )
            session.save()
        return redirect(f"/negotiation/chat/{session.id}/")

    # Seller path: only allowed if buyer already started (session exists)
    # OR negotiation mode with price below trigger
    if userid == quote.seller_id:
        if session:
            return redirect(f"/negotiation/chat/{session.id}/")
        try:
            if getattr(req, 'negotiation_mode', None) == "negotiation" and getattr(req, 'negotiation_trigger_price', None) is not None:
                if float(quote.price) < float(req.negotiation_trigger_price):
                    session = ChatSession(
                        quote_id=str(quote.id),
                        buyer_id=req.buyerid,
                        seller_id=quote.seller_id
                    )
                    session.save()
                    return redirect(f"/negotiation/chat/{session.id}/")
        except Exception:
            pass
        return redirect("/users/dashboard")

    # Others: not allowed
    return redirect("/users/dashboard")


def chat_room_view(request, session_id):
    userid = request.session.get("userid")
    if not userid:
        return redirect("/users/login")

    session = ChatSession.objects(id=session_id).first()
    if not session:
        return redirect("/users/dashboard")

    # Permission: only participants
    if userid not in [session.buyer_id, session.seller_id]:
        return redirect("/users/dashboard")

    messages = ChatMessage.objects(session_id=session).order_by('timestamp')

    # Determine counterparty to display in header
    counterparty = session.seller_id if userid == session.buyer_id else session.buyer_id

    return render(request, "negotiation/chat_room.html", {
        "session": session,
        "messages": messages,
        "userid": userid,
        "counterparty": counterparty,
    })


@csrf_exempt
def send_message_view(request, session_id):
    if request.method == "POST":
        session = ChatSession.objects(id=session_id).first()
        sender_id = request.session.get("userid")
        if not sender_id or not session or sender_id not in [session.buyer_id, session.seller_id]:
            return redirect("/users/login")
        message_text = request.POST.get("message", "")

        file = request.FILES.get("file")
        file_url = None
        file_type = None
        original_filename = None

        if file:
            filename = f"{uuid.uuid4()}_{file.name}"
            folder = os.path.join(settings.MEDIA_ROOT, 'chat_uploads')
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, filename)

            with open(path, 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

            file_url = f"/media/chat_uploads/{filename}"
            file_type = file.content_type
            original_filename = file.name

        ChatMessage(
            session_id=session,
            sender_id=sender_id,
            message=message_text,
            file_url=file_url,
            file_type=file_type,
            original_filename=original_filename,
            timestamp=datetime.now()
        ).save()

    return redirect(f"/negotiation/chat/{session_id}/")


@csrf_exempt
def upload_chat_file_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        filename = f"{uuid.uuid4()}_{file.name}"
        folder = os.path.join(settings.MEDIA_ROOT, 'chat_uploads')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)

        with open(path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        return JsonResponse({
            'success': True,
            'file_url': f"/media/chat_uploads/{filename}",
            'file_type': file.content_type,
            'original_filename': file.name
        })

    return JsonResponse({'success': False, 'error': 'No file received'})


def chat_messages_partial(request, session_id):
    session = ChatSession.objects(id=session_id).first()
    messages = ChatMessage.objects(session_id=session).order_by('timestamp')
    return render(request, "negotiation/partials/chat_messages.html", {
        "messages": messages,
        "userid": request.session.get("userid")
    })


def chat_dashboard_view(request):
    userid = request.session.get("userid")
    if not userid:
        return redirect("/users/login")

    sessions = ChatSession.objects.filter(
        __raw__={"$or": [{"buyer_id": userid}, {"seller_id": userid}]}
    ).order_by("-created_on")

    session_data = []
    for s in sessions:
        quote = None
        requirement = None
        try:
            if getattr(s, 'quote_id', None):
                quote = Quote.objects(id=str(s.quote_id)).first()
                if quote and getattr(quote, 'req_id', None):
                    requirement = Requirement.objects(id=str(quote.req_id)).first()
        except Exception:
            quote = None
            requirement = None

        # If a deal exists for this requirement, only keep the session whose quote matches the deal
        try:
            if requirement:
                deal = Deal.objects(requirement_id=str(requirement.id)).first()
                if deal and str(deal.quote_id) != (str(quote.id) if quote else ""):
                    continue
        except Exception:
            pass

        # Determine role for grouping in template
        role = None
        if s.buyer_id == userid:
            role = "buyer"
        elif s.seller_id == userid:
            role = "seller"
        else:
            continue

        session_data.append({
            "session": s,
            "quote": quote,
            "requirement": requirement,
            "role": role,
        })

    return render(request, "negotiation/chat_dashboard.html", {
        "session_data": session_data,
        "userid": userid
    })
