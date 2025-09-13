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
     - `DATABASE_URL` — Postgres DSN, e.g. `postgresql://USER:PASSWORD@localhost:5432/fitness_ai`
       - If using older `postgres://` DSN, it is auto-upgraded to `postgresql://`.
     - Optional OAuth keys (Google/GitHub/Strava) can remain empty for now.

4. Initialize the database (Flask-Migrate):
   - Ensure `FLASK_APP=backend.app` is present in your `.env`
   - `flask db init`        # once per project
   - `flask db migrate -m "initial"`
   - `flask db upgrade`

5. Run the app:
   - `flask run`
