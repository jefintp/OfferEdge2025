from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from negotiation.models import ChatSession, ChatMessage
from deals.models import Quote
from requirements.models import Requirement
from datetime import datetime
from bson import ObjectId

def start_chat_view(request, quote_id):
    userid = request.session.get("userid")
    quote = Quote.objects(id=quote_id).first()
    if not quote or not userid:
        return redirect("/users/dashboard")

    req = Requirement.objects(id=quote.req_id).first()
    if not req:
        return redirect("/users/dashboard")

    session = ChatSession.objects(quote_id=str(quote.id)).first()
    if not session:
        session = ChatSession(
            quote_id=str(quote.id),
            buyer_id=req.buyerid,
            seller_id=quote.seller_id
        )
        session.save()

    return redirect(f"/negotiation/chat/{session.id}/")


def chat_room_view(request, session_id):
    session = ChatSession.objects(id=session_id).first()
    messages = ChatMessage.objects(session_id=session).order_by('timestamp')
    return render(request, "negotiation/chat_room.html", {
        "session": session,
        "messages": messages,
        "userid": request.session.get("userid")
    })


@csrf_exempt
def send_message_view(request, session_id):
    if request.method == "POST":
        ChatMessage(
            session_id=ChatSession.objects(id=session_id).first(),
            sender_id=request.session.get("userid"),
            message=request.POST.get("message")
        ).save()
    return redirect(f"/negotiation/chat/{session_id}/")


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
        quote = Quote.objects(id=s.quote_id).first()
        session_data.append({
            "session": s,
            "quote": quote
    })


    return render(request, "negotiation/chat_dashboard.html", {
        "session_data": session_data,

        "userid": userid
    })