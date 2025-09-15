from flask import Blueprint, request, jsonify, g
from sqlalchemy import func

from ..auth import jwt_required, json_form_required
from ..forms import ActivityForm, ActivityUpdateForm
from ..models import db, Activity, ActivityCategory


bp = Blueprint('activities', __name__)


@bp.post('/me/activities')
@jwt_required
@json_form_required(ActivityForm)
def log_activity():
    user = g.current_user
    form = g.form

    # Resolve category via id or name
    cat_obj = None
    if form.category_id.data:
        cat_obj = ActivityCategory.query.get(form.category_id.data)
        if not cat_obj:
            return jsonify(message='Category not found'), 400
    elif form.category.data:
        name = form.category.data.strip()
        cat_obj = ActivityCategory.query.filter(func.lower(ActivityCategory.name) == name.lower()).one_or_none()
        if not cat_obj:
            return jsonify(message='Category not found'), 400
    else:
        return jsonify(message='category_id or category is required'), 400

    activity = Activity(
        title=form.title.data,
        distance=form.distance.data,
        duration=form.duration.data,
        notes=form.notes.data or None,
        user_id=user.id,
        time=form.time.data,
        complete=bool(form.complete.data),
        category_id=cat_obj.id,
    )

    db.session.add(activity)
    db.session.commit()

    payload = {
        "id": activity.id,
        "title": activity.title,
        "category_id": activity.category_id,
        "category": activity.category.name if activity.category else None,
        "distance": activity.distance,
        "duration": activity.duration.isoformat() if activity.duration else None,
        "notes": activity.notes,
        "user_id": activity.user_id,
        "time": activity.time.isoformat() if activity.time else None,
        "complete": activity.complete,
    }

    return jsonify(activity=payload), 201


@bp.get('/me/activities')
@jwt_required
def list_my_activities():
    user = g.current_user

    q = Activity.query.filter(Activity.user_id == user.id)

    category_id = request.args.get('category_id', type=int)
    if category_id is not None:
        q = q.filter(Activity.category_id == category_id)

    complete_param = request.args.get('complete')
    if complete_param is not None:
        val = complete_param.strip().lower()
        if val in ('true', '1', 'yes'):
            q = q.filter(Activity.complete.is_(True))
        elif val in ('false', '0', 'no'):
            q = q.filter(Activity.complete.is_(False))

    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    limit = max(1, min(100, limit or 50))
    offset = max(0, offset or 0)

    activities = q.order_by(Activity.id.desc()).offset(offset).limit(limit).all()

    def _act_payload(a: Activity):
        return {
            "id": a.id,
            "title": a.title,
            "category_id": a.category_id,
            "category": a.category.name if a.category else None,
            "distance": a.distance,
            "duration": a.duration.isoformat() if a.duration else None,
            "notes": a.notes,
            "user_id": a.user_id,
            "time": a.time.isoformat() if a.time else None,
            "complete": a.complete,
        }

    return jsonify(activities=[_act_payload(a) for a in activities], count=len(activities))


@bp.get('/me/activities/<int:activity_id>')
@jwt_required
def get_my_activity(activity_id: int):
    user = g.current_user
    a = (
        Activity.query
        .filter(Activity.id == activity_id, Activity.user_id == user.id)
        .one_or_none()
    )
    if not a:
        return jsonify(message="Activity not found"), 404
    payload = {
        "id": a.id,
        "title": a.title,
        "category_id": a.category_id,
        "category": a.category.name if a.category else None,
        "distance": a.distance,
        "duration": a.duration.isoformat() if a.duration else None,
        "notes": a.notes,
        "user_id": a.user_id,
        "time": a.time.isoformat() if a.time else None,
        "complete": a.complete,
    }
    return jsonify(activity=payload)


@bp.patch('/me/activities/<int:activity_id>')
@jwt_required
@json_form_required(ActivityUpdateForm)
def update_my_activity(activity_id: int):
    user = g.current_user
    received = g.json
    form = g.form

    activity = Activity.query.filter(
        Activity.id == activity_id, Activity.user_id == user.id
    ).one_or_none()
    if not activity:
        return jsonify(message="Activity not found"), 404

    # Title
    if 'title' in received and received['title'] is not None:
        activity.title = form.title.data

    # Category resolution
    if 'category_id' in received or 'category' in received:
        cat_obj = None
        if 'category_id' in received and received['category_id'] is not None:
            cat_obj = ActivityCategory.query.get(form.category_id.data)
            if not cat_obj:
                return jsonify(message='Category not found'), 400
        elif 'category' in received and received['category']:
            name = form.category.data.strip()
            cat_obj = ActivityCategory.query.filter(
                func.lower(ActivityCategory.name) == name.lower()
            ).one_or_none()
            if not cat_obj:
                return jsonify(message='Category not found'), 400
        if cat_obj:
            activity.category_id = cat_obj.id

    # Distance
    if 'distance' in received and received['distance'] is not None:
        activity.distance = form.distance.data

    # Duration
    if 'duration' in received and received['duration']:
        activity.duration = form.duration.data

    # Time
    if 'time' in received and received['time']:
        activity.time = form.time.data

    # Notes
    if 'notes' in received:
        activity.notes = received['notes'] or None

    # Complete
    if 'complete' in received:
        activity.complete = bool(form.complete.data)

    db.session.commit()

    payload = {
        "id": activity.id,
        "title": activity.title,
        "category_id": activity.category_id,
        "category": activity.category.name if activity.category else None,
        "distance": activity.distance,
        "duration": activity.duration.isoformat() if activity.duration else None,
        "notes": activity.notes,
        "user_id": activity.user_id,
        "time": activity.time.isoformat() if activity.time else None,
        "complete": activity.complete,
    }
    return jsonify(activity=payload)


@bp.delete('/me/activities/<int:activity_id>')
@jwt_required
def delete_my_activity(activity_id: int):
    user = g.current_user
    activity = Activity.query.filter(
        Activity.id == activity_id, Activity.user_id == user.id
    ).one_or_none()
    if not activity:
        return jsonify(message="Activity not found"), 404
    db.session.delete(activity)
    db.session.commit()
    return "", 204


@bp.route("/api/activities/<int:activity_id>", methods=["DELETE"])  # legacy path
@jwt_required
def delete_activity(activity_id: int):
    user = g.current_user
    activity = Activity.query.filter(
        Activity.id == activity_id, Activity.user_id == user.id
    ).one_or_none()
    if not activity:
        return jsonify(message="Activity not found"), 404
    db.session.delete(activity)
    db.session.commit()
    return "", 204

