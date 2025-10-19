from requirements.models import Requirement
from quotes.models import Quote
from deals.models import Deal
from negotiation.models import ChatSession, ChatMessage
def delete_requirement_and_related(req_id, user_id, is_admin):
    if not req_id or not user_id:
        return False, "Invalid request or user not authenticated."

    try:
        requirement = Requirement.objects.get(id=req_id)

        # 🔐 Permission check
        if not is_admin and str(requirement.buyerid) != str(user_id):
            return False, "You are not authorized to delete this requirement."

        # 🧹 Cascade delete
        # Delete chats linked to quotes under this requirement
        quotes = list(Quote.objects(req_id=str(requirement.id)))
        for q in quotes:
            sessions = ChatSession.objects(quote_id=str(q.id))
            for s in sessions:
                ChatMessage.objects(session_id=s).delete()
                s.delete()
        # Delete quotes and deals
        Quote.objects(req_id=str(requirement.id)).delete()
        Deal.objects(requirement_id=str(requirement.id)).delete()
        # Delete requirement
        requirement.delete()

        return True, "Requirement and related data deleted successfully."

    except Requirement.DoesNotExist:
        return False, "Requirement not found."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"