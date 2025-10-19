from django.core.management.base import BaseCommand
from datetime import datetime

from requirements.models import Requirement
from quotes.models import Quote
from deals.models import Deal


def _deadline_passed(deadline):
    try:
        if getattr(deadline, 'tzinfo', None) is not None:
            return deadline <= datetime.now(deadline.tzinfo)
        return deadline <= datetime.now()
    except Exception:
        return False

class Command(BaseCommand):
    help = "Auto-finalize deals for requirements in lowest_bid mode whose deadlines have passed"

    def handle(self, *args, **options):
        now = datetime.now()
        finalized_count = 0
        checked = 0

        # Fetch lowest_bid requirements and compare deadline in Python to avoid tz mismatches
        try:
            reqs = list(Requirement.objects(negotiation_mode="lowest_bid"))
        except Exception:
            reqs = []

        for req in reqs:
            checked += 1
            req_id_str = str(req.id)

            if not getattr(req, 'deadline', None) or not _deadline_passed(req.deadline):
                continue

            # Skip if a deal already exists for this requirement
            if Deal.objects(requirement_id=req_id_str).first():
                continue

            # Gather quotes
            quotes = list(Quote.objects(req_id=req_id_str))
            if not quotes:
                continue

            # Pick lowest price; tie-breaker by earliest createdon
            def q_key(q):
                try:
                    price = float(q.price)
                except Exception:
                    price = float("inf")
                created = getattr(q, "createdon", None)
                return (price, created or now)

            quotes.sort(key=q_key)
            best = quotes[0]

            # Finalize the chosen quote and create a Deal
            try:
                best.finalized = True
                best.save()

                Deal(
                    quote_id=str(best.id),
                    requirement_id=req_id_str,
                    buyer_id=req.buyerid,
                    seller_id=best.seller_id,
                    finalized_by="system",
                    method="auto",
                    finalized_on=now,
                ).save()

                finalized_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to finalize for requirement {req_id_str}: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS(
            f"Checked {checked} requirements; auto-finalized {finalized_count} deal(s)."
        ))
