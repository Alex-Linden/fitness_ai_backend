from typing import Optional, Dict, Any, Type, Callable
from functools import wraps
from flask import current_app, request, jsonify, g
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


def jwt_required(fn: Callable) -> Callable:
    """Decorator that enforces JWT auth and loads g.current_user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify(message='Missing or invalid Authorization header'), 401

        token = auth_header.split(' ', 1)[1].strip()
        payload = decode_access_token(token)
        if payload is None or 'email' not in payload:
            return jsonify(message='Invalid or expired token'), 401

        # Lazy import to avoid circular deps
        from .models import User
        user = User.query.filter_by(email=payload['email']).one_or_none()
        if not user:
            return jsonify(message='User not found'), 404

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def json_form_required(form_cls: Type) -> Callable:
    """Decorator that parses JSON body into a WTForms form and validates it.

    On success, attaches `g.json` and `g.form` for downstream use.
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            form = form_cls(csrf_enabled=False, data=data)
            if not form.validate_on_submit():
                return jsonify(errors=form.errors), 400
            g.json = data
            g.form = form
            return fn(*args, **kwargs)

        return wrapper

    return decorator
