from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..models import ActivityCategory


bp = Blueprint('categories', __name__)


@bp.get('/activity-categories')
def list_activity_categories():
    q = request.args.get('q', type=str)
    query = ActivityCategory.query
    if q:
        query = query.filter(ActivityCategory.name.ilike(f"%{q}%"))
    cats = query.order_by(ActivityCategory.name.asc()).all()
    return jsonify(categories=[c.serialize() for c in cats])

