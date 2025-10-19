# OfferEdge – Project Summary

This document provides a concise, high-level overview of the OfferEdge marketplace web app and its main functionalities, architecture, and flows. It’s intended for developers, PMs, and moderators to understand the system at a glance.

## Stack and Architecture
- Framework: Django (views/templates), MongoEngine (MongoDB Documents), HTMX for partial updates, TailwindCSS (via CDN) for styling.
- Background jobs: Celery + Celery Beat (default schedule every 1 minute) with Redis broker (configurable via env).
- Apps: users, requirements, quotes, negotiation, deals, moderation, feedback.
- Templates live under `Template/`; static via CDN; media uploaded under `MEDIA_ROOT` (e.g., `media/chat_uploads`, `media/requirement_uploads`, `media/quote_uploads`).
- Channels present for ASGI routing but real-time chat currently uses polling/HTMX.

## Core Data Models (MongoEngine Documents)
- users.User: custom user with `userid`, `password_hash`, flags (`is_admin`, `is_banned`).
- requirements.Requirement: buyerid, title, description, quantity, expectedPriceRange, deadline, createdAt, category (service/product), location (normalized lowercase), negotiation_mode (lowest_bid/negotiation), negotiation_trigger_price, attachment_url/type/name, moderation flags.
- quotes.Quote: req_id, seller_id, price, deliveryTimeline, notes, createdon, finalized, attachment_url/type/name.
- deals.Deal: quote_id, requirement_id, buyer_id, seller_id, finalized_on, finalized_by, method (auto/manual).
- negotiation.ChatSession: quote_id, buyer_id, seller_id, created_on.
- negotiation.ChatMessage: session_id, sender_id, message, timestamp, file_url/type/original_filename.
- moderation.Report: deal_id, reporter_id, reported_id, requirement_id, quote_id, reason, status, created_at.

## Roles
- Buyer: posts requirements, reviews quotes, negotiates, finalizes deals, can report counterparty post-finalization.
- Seller: explores requirements, places quotes with attachments, negotiates per rules, can report counterparty post-finalization.
- Admin/Moderator: moderation dashboard with user/requirement/quote management and report triage.

## Major Features & Flows

### Authentication
- Simple signup/login; session keys: `userid`, `is_admin` (coerced to boolean). Logout flushes session.

### Post Requirement (Buyer)
- Form fields: title, description, quantity, expected price range, deadline (validated > now), category (service/product), location (lowercased, UI title-cased), negotiation mode (lowest_bid or negotiation with trigger price), optional attachment.
- Duplicate prevention: idempotency nonce + server-side de-dup by (buyer, title, deadline).
- Client-side: disables submit on first click to avoid double-submit.

### Explore Requirements (Seller)
- Cards show: title (highlight with gradient/blue), description inline, price, quantity, deadline, category/location chips, and buyer attachment (image preview or download).
- Filters: category (service/product), location (Kerala suggestions via datalist; case-insensitive match), title search (case-insensitive substring) — all live via HTMX.
- Dynamic updates: HTMX pushes URL and updates results without Apply clicks.
- Exclusions: hides buyer’s own requirements and any requirement the seller already quoted (reappears when quote is deleted).
- CTA: “Place a Quote.” Removed separate “View details” in explore cards per spec.

### Place Quote (Seller)
- One quote per requirement per seller; cannot quote own requirement.
- Fields: price, delivery timeline, notes, optional attachment (image or file).

### Negotiation (Chat)
- Start chat rules:
  - Buyer: may open chat for any quote before finalization. After finalization, only the finalized seller quote is allowed.
  - Seller: may chat if buyer already started (existing session) or if negotiation_mode=negotiation and seller price < trigger price.
- Start Negotiation button is hidden for finalized quotes on the dashboard.
- Chat room: messages and file uploads (images inline, other files downloadable). Messages refresh via HTMX partial.
- Negotiations dashboard: grouped Buy/Sell sessions, respecting finalization restrictions.

### Finalized Deals
- List split into Buy/Sell, with requirement title, counterparty, amount, time, last message.
- Open Chat for the pair.
- Report button to report counterparty (goes to moderation).
- Auto-finalization: in lowest_bid mode only, after deadline. Picks lowest price and creates Deal with method=auto. Triggered by Celery Beat every 1 minute (or via the management command).

### Moderation
- Dashboard sections:
  - Users: search (hidden until searched), ban/unban/delete (admins protected), buyer/seller flags.
  - Requirements: list with delete (cascades quotes/deals/chats via utility), flagged info.
  - Quotes: finalize/delete admin actions.
  - Reports: recent user reports from finalized deals; detail view with reason and context.
- Actions are CSRF-protected and POST-only where appropriate.

## Deletion & Cascades
- Deleting a Requirement cascades to its Quotes, any Deal, and related Negotiation ChatSessions/Messages.
- Quote deletion blocked if finalized or if a Deal exists for that quote.

## UX & Design System
- Futuristic, minimal, glassmorphism-inspired surfaces (rounded cards, light shadows, gradient accents).
- Consistent navbar with gradient background and pill highlights; responsive layouts; accessible focus styles.
- Explore redesigned with modern cards and responsive filters.

## URLs (Highlights)
- Home: `/`
- Users: `/users/login`, `/users/signup`, `/logout`, `/dashboard`
- Requirements: `/requirements/post`, `/requirements/detail/<id>`, `/requirements/my`
- Quotes: `/quotes/explore`, `/quotes/place/<reqid>`, `/quotes/my`
- Negotiation: `/negotiation/chat/<session_id>`, `/negotiation/chat/start/<quote_id>`, `/negotiation/`
- Deals: `/deals/finalized/`, `/deals/finalize/<quote_id>` (POST)
- Moderation: `/moderation/` + actions; Reports: `/moderation/report/<deal_id>` (create, participants) and `/moderation/reports/<report_id>` (admin view)
- Background tasks: Celery Beat auto-finalization (every 1 minute); Management command alternative: `python manage.py auto_finalize_deals`.

## Operational Notes
- Media upload locations must be served via Django’s `MEDIA_URL` in development.
- Timezone: the app operates in Indian Standard Time (Asia/Kolkata) with naive local datetimes (`USE_TZ=False`). Deadlines and auto-finalization compare against local time.
- Celery: broker defaults to `redis://localhost:6379/0` (override with `CELERY_BROKER_URL`), beat runs the auto-finalization task every 1 minute.
- Security: participant-only access enforced for chats and report creation; admin-only moderation routes; admin user protection from moderation actions.

## Future Improvements (Suggestions)
- WebSocket chat (Channels consumers) for real-time messaging and typing indicators.
- Pagination for Explore, My Quotes, and Moderation lists.
- Rate-limiting and categorization for Reports; admin workflow to resolve/close.
- Email/notification system for deal finalization and report updates.
- File type and size validations for uploads; virus scanning hooks if needed.

This summary complements `WARP.md` (commands and architecture tips). For any missing details, review app-specific `views.py` and templates under `Template/`.
