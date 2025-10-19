from celery import shared_task
from datetime import datetime
from requirements.models import Requirement
from quotes.models import Quote
from deals.models import Deal


def _deadline_passed(deadline):
    try:
        if getattr(deadline, 'tzinfo', None) is not None:
            # Compare in the same timezone as the stored value
            return deadline <= datetime.now(deadline.tzinfo)
        return deadline <= datetime.now()
    except Exception:
        return False

@shared_task
def auto_finalize_deals_task():
    now = datetime.now()
    finalized_count = 0


    # Fetch by mode only; perform deadline comparison in Python to avoid tz mismatches
    try:
        reqs = list(Requirement.objects(negotiation_mode="lowest_bid"))
    except Exception:
        reqs = []

    for req in reqs:
        # Skip if not past deadline
        if not getattr(req, 'deadline', None) or not _deadline_passed(req.deadline):
            continue
        # Skip if already finalized
        if Deal.objects(requirement_id=str(req.id)).first():
            continue

        quotes = list(Quote.objects(req_id=str(req.id)))
        if not quotes:
            continue

        def q_key(q):
            try:
                price = float(q.price)
            except Exception:
                price = float('inf')
            created = getattr(q, 'createdon', None)
            return (price, created or now)

        quotes.sort(key=q_key)
        best = quotes[0]
        try:
            best.finalized = True
            best.save()
            Deal(
                quote_id=str(best.id),
                requirement_id=str(req.id),
                buyer_id=req.buyerid,
                seller_id=best.seller_id,
                finalized_by="system",
                method="auto",
                finalized_on=now,
            ).save()
            finalized_count += 1
        except Exception:
            continue

    return finalized_count
