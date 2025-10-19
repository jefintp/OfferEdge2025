# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Stack: Django (5.x), MongoEngine + MongoDB, Tailwind CSS, HTMX. Channels is present for ASGI routing, but current chat UI polls via HTMX.
- Entry points:
  - Django settings/urls: offeredge_core/settings.py, offeredge_core/urls.py, offeredge_core/asgi.py, offeredge_core/wsgi.py
  - Home: offeredge_core/homeurl.py → offeredge_core/views.py:home → Template/home.html
  - Apps: users, requirements, quotes, deals, negotiation, moderation, feedback
- Templates and static:
  - Templates under Template/ (shared bases: base.html, base_logged_in.html)
  - Static files served from Static/ during development; media uploads saved under media/ (MEDIA_ROOT)
- Data modeling:
  - Uses MongoEngine Document classes (not Django ORM). IDs are stored as strings across documents (e.g., Quote.req_id stores Requirement.id as a string).
  - Key documents: users.User, requirements.Requirement, quotes.Quote, deals.Deal, negotiation.ChatSession, negotiation.ChatMessage
- Auth/session model:
  - Custom user model stored in MongoDB; bcrypt for passwords
  - Session keys: 'userid' (required for most views), 'is_admin' (string-to-bool conversion used at login)
  - Admin-only views decorated with users.decorators.admin_required

Common commands
- Backend (Django)
  - Run dev server:
    - python manage.py runserver
  - Django shell:
    - python manage.py shell
  - Run all tests:
    - python manage.py test
  - Run a single test (example path):
    - python manage.py test users.tests.TestUserAuth.test_login_flow
  - Auto-finalize past-deadline lowest-bid deals (management command):
    - python manage.py auto_finalize_deals
    - Schedule periodically (e.g., cron/Task Scheduler) to run every few minutes

- Frontend styles (Tailwind CSS)
  - Install JS dependencies (required for CLI-based builds):
    - npm install
  - Dev watch build (writes compiled CSS to Static/dist/main.css):
    - npx tailwindcss -i ./Static/src/main.css -o ./Static/dist/main.css --watch
  - One-off minified build:
    - npx tailwindcss -i ./Static/src/main.css -o ./Static/dist/main.css --minify
  - Notes:
    - tailwind.config.js scans .html and .py files repo-wide; postcss.config.js enables Tailwind + Autoprefixer
    - Many templates load Tailwind via CDN; the CLI build is optional but recommended for consistent styling without CDN

High-level architecture and flows
- User onboarding (users app)
  - signup_view/login_view manage bcrypt-hashed credentials in MongoDB
  - dashboard_view aggregates buyer and seller perspectives in one page

- Requirements and quotes (requirements, quotes, deals apps)
  - Buyer posts Requirement via RequirementForm (negotiation_mode: lowest_bid or negotiation; optional negotiation_trigger_price)
  - Sellers browse in quotes/explore, place quotes with optional file attachment
  - Buyer finalizes a quote → Deal document is created; quotes can also be auto-finalized after deadline if negotiation is disabled

- Negotiation/chat (negotiation app)
  - start_chat_view creates a ChatSession for a quote; chat_room_view renders messages
  - Messages are periodically refreshed using HTMX (negotiation/partials/chat_messages.html)
  - File uploads are stored under media/chat_uploads and served via MEDIA_URL
  - Channels routing is defined (negotiation/routing.py), but no consumers are present; real-time WebSocket is not currently in use

- Moderation (moderation app)
  - moderation_dashboard renders user/requirement/quote overview
  - Admin actions: ban/unban/delete users; finalize/delete quotes

Conventions and important notes
- MongoDB connection is configured directly in offeredge_core/settings.py via mongoengine.connect; update appropriately for your environment
- STATICFILES_DIRS includes Static; ensure compiled CSS (if using Tailwind CLI) is emitted under Static/ (e.g., Static/dist/main.css)
- URL structure is centralized in offeredge_core/urls.py and app-level urls.py files; Template pages live in Template/ and app-specific subfolders
- No repo-level linter or formatter configuration was found; use your local defaults if needed
