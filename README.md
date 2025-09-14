# Fitness AI

A personal project built using Flask to create a web application for generating personalized workout plans and tracking fitness progress.

## Installation

1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`  (Windows: ` .venv\Scripts\activate`)

2. Install backend requirements:
   - `pip install -r backend/requirements.txt`

3. Configure environment variables (.env):
   - Copy `.env.example` to `.env` and adjust values:
     - `cp .env.example .env`
   - Key variables:
     - `SECRET_KEY` — any strong random string
     - `DATABASE_URL` — Postgres DSN using psycopg3, e.g. `postgresql+psycopg://USER:PASSWORD@localhost:5432/fitness_ai`
       - If using older `postgres://` DSN, the app upgrades it to `postgresql+psycopg://` automatically.
     - Optional OAuth keys (Google/GitHub/Strava) can remain empty for now.

4. Initialize the database (Flask-Migrate):
   - Ensure `FLASK_APP=backend.app` is present in your `.env`
   - `flask db init`        # once per project
   - `flask db migrate -m "initial"`
   - `flask db upgrade`

5. Run the app:
   - `flask run` (port is set via `.env` to 5001)

## Seeding sample data

Populate categories, users, and activities for local testing:

- Option A: `flask seed`
- Option B: `python backend/seed.py`

This creates two users with password `password123` and prints ready-to-use JWTs for Insomnia:

- `test.user1@example.com` — includes a Morning Run and Evening Yoga
- `john.doe@example.com` — includes a Lunch Ride and Pool Swim
