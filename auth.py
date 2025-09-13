from typing import Optional, Dict, Any
from flask import current_app
import jwt


def create_access_token(email: str) -> str:
    """Create a signed JWT for the given user email."""
    payload = {"email": email}
    secret = current_app.config.get("SECRET_KEY")
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT and return its payload, or None on failure."""
    secret = current_app.config.get("SECRET_KEY")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        return None

