from flask import Blueprint, jsonify, g, request
from sqlalchemy import func

from ..auth import jwt_required, json_form_required
from ..forms import UserEditForm, PasswordChangeForm, DeleteAccountForm
from ..models import db, bcrypt, PasswordChangeLog
from ..auth import create_access_token
from datetime import datetime, timedelta


bp = Blueprint('users', __name__)


@bp.get('/me')
@jwt_required
def me():
    return jsonify(user=g.current_user.serialize())


@bp.patch('/me')
@jwt_required
@json_form_required(UserEditForm)
def update_me():
    user = g.current_user
    received = g.json
    form = g.form

    old_email = user.email

    if 'email' in received and received['email']:
        user.email = received['email']
    if 'first_name' in received and received['first_name']:
        user.first_name = received['first_name']
    if 'last_name' in received and received['last_name']:
        user.last_name = received['last_name']
    if 'birthday' in received and received['birthday']:
        user.birthday = form.birthday.data
    if 'weight' in received and received['weight'] is not None:
        user.weight = form.weight.data
    if 'gender' in received and received['gender']:
        user.gender = received['gender']
    if 'benchmarks' in received:
        benchmarks = received['benchmarks']
        if isinstance(benchmarks, str):
            try:
                import json as _json
                benchmarks = _json.loads(benchmarks)
            except Exception:
                benchmarks = None
        user.benchmarks = benchmarks
    if 'password' in received and received['password']:
        from ..models import bcrypt as _bcrypt
        user.password = _bcrypt.generate_password_hash(received['password']).decode('UTF-8')

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(message='Email already in use'), 409

    new_token = None
    if user.email != old_email:
        new_token = create_access_token(user.email)

    result = {"user": user.serialize()}
    if new_token:
        result["token"] = new_token
    return jsonify(result)


@bp.patch('/me/password')
@jwt_required
@json_form_required(PasswordChangeForm)
def change_password():
    user = g.current_user
    received = g.json
    form = g.form

    current_password = received.get('current_password')
    new_password = received.get('new_password')

    window = datetime.utcnow() - timedelta(minutes=15)
    failed_count = db.session.query(func.count(PasswordChangeLog.id)).filter(
        PasswordChangeLog.user_id == user.id,
        PasswordChangeLog.success.is_(False),
        PasswordChangeLog.created_at >= window,
    ).scalar() or 0
    if failed_count >= 5:
        return jsonify(message='Too many failed attempts. Try again in 15 minutes'), 429

    if not bcrypt.check_password_hash(user.password, current_password):
        log = PasswordChangeLog(user_id=user.id, ip=request.remote_addr, success=False)
        db.session.add(log)
        db.session.commit()
        return jsonify(message='Current password is incorrect'), 401

    if bcrypt.check_password_hash(user.password, new_password):
        return jsonify(message='New password must be different from current password'), 400

    user.password = bcrypt.generate_password_hash(new_password).decode('UTF-8')
    log = PasswordChangeLog(user_id=user.id, ip=request.remote_addr, success=True)
    db.session.add(log)
    db.session.commit()

    return jsonify(message='Password updated successfully')


@bp.delete('/me')
@jwt_required
@json_form_required(DeleteAccountForm)
def delete_me():
    user = g.current_user
    received = g.json

    current_password = received.get('current_password')
    confirm_email = received.get('confirm_email')

    if confirm_email != user.email:
        return jsonify(message='Confirmation email does not match'), 400

    if not bcrypt.check_password_hash(user.password, current_password):
        return jsonify(message='Current password is incorrect'), 401

    db.session.delete(user)
    db.session.commit()

    return jsonify(message='Account deleted'), 200

