"""Seed the database with sample users, categories, and activities.

Usage:
  python backend/seed.py

Requires env vars (see backend/.env):
  - DATABASE_URL
  - SECRET_KEY
"""

from datetime import time
from typing import List

from backend.app import app
from backend.models import db, User, Activity, ActivityCategory, bcrypt
from backend.auth import create_access_token


def ensure_categories(names: List[str]) -> None:
    for n in names:
        existing = ActivityCategory.query.filter(ActivityCategory.name.ilike(n)).one_or_none()
        if not existing:
            db.session.add(ActivityCategory(name=n))
    db.session.commit()


def get_category(name: str) -> ActivityCategory:
    cat = ActivityCategory.query.filter(ActivityCategory.name.ilike(name)).one_or_none()
    if not cat:
        cat = ActivityCategory(name=name)
        db.session.add(cat)
        db.session.commit()
    return cat


def upsert_user(email: str, password: str, first_name: str, last_name: str) -> User:
    user = User.query.filter_by(email=email).one_or_none()
    if user:
        # Reset to known values for testing
        user.first_name = first_name
        user.last_name = last_name
        user.password = bcrypt.generate_password_hash(password).decode('UTF-8')
    else:
        user = User.signup(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
    db.session.commit()
    return user


def reset_activities_for_user(user: User) -> None:
    Activity.query.filter_by(user_id=user.id).delete()
    db.session.commit()


def add_activity(user: User, title: str, category_name: str, distance: float, duration_hms: str, time_hms: str, notes: str = None, complete: bool = True):
    # parse HH:MM:SS
    def parse_hms(s: str) -> time:
        hh, mm, ss = [int(x) for x in s.split(':')]
        return time(hour=hh, minute=mm, second=ss)

    cat = get_category(category_name)
    act = Activity(
        title=title,
        category_id=cat.id,
        distance=float(distance),
        duration=parse_hms(duration_hms),
        time=parse_hms(time_hms),
        notes=notes,
        complete=bool(complete),
        user_id=user.id,
    )
    db.session.add(act)
    db.session.commit()
    return act


def main():
    with app.app_context():
        # Ensure core categories exist
        ensure_categories(["Run", "Bike", "Swim", "Weight Training", "Yoga"]) 

        # Create or update sample users
        user1 = upsert_user("test.user1@example.com", "password123", "Jane", "Doe")
        user2 = upsert_user("john.doe@example.com", "password123", "John", "Doe")

        # Reset and add activities for user1
        reset_activities_for_user(user1)
        add_activity(user1, "Morning Run", "Run", 5.0, "00:42:30", "06:30:00", notes="Tempo run", complete=True)
        add_activity(user1, "Evening Yoga", "Yoga", 0.0, "00:30:00", "19:00:00", notes="Vinyasa flow", complete=True)

        # Reset and add activities for user2
        reset_activities_for_user(user2)
        add_activity(user2, "Lunch Ride", "Bike", 12.5, "00:50:00", "12:15:00", notes="Windy", complete=True)
        add_activity(user2, "Pool Swim", "Swim", 1.2, "00:40:00", "07:00:00", notes="Drills", complete=False)

        # Print ready-to-use JWTs for testing in Insomnia
        token1 = create_access_token(user1.email)
        token2 = create_access_token(user2.email)
        print("Seed complete. Test users and tokens:")
        print(f"- {user1.email} / password123")
        print(f"  Bearer {token1}")
        print(f"- {user2.email} / password123")
        print(f"  Bearer {token2}")


if __name__ == "__main__":
    main()

