from flask import jsonify
from werkzeug.exceptions import HTTPException


def _json_error(status_code: int, message: str, **extra):
    payload = {"error": {"code": status_code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return jsonify(payload), status_code


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(err):
        msg = err.description if isinstance(err, HTTPException) else "Bad Request"
        return _json_error(400, msg)

    @app.errorhandler(401)
    def unauthorized(err):
        msg = err.description if isinstance(err, HTTPException) else "Unauthorized"
        return _json_error(401, msg)

    @app.errorhandler(403)
    def forbidden(err):
        msg = err.description if isinstance(err, HTTPException) else "Forbidden"
        return _json_error(403, msg)

    @app.errorhandler(404)
    def not_found(err):
        msg = err.description if isinstance(err, HTTPException) else "Not Found"
        return _json_error(404, msg)

    @app.errorhandler(405)
    def method_not_allowed(err):
        msg = err.description if isinstance(err, HTTPException) else "Method Not Allowed"
        return _json_error(405, msg)

    @app.errorhandler(422)
    def unprocessable_entity(err):
        msg = err.description if isinstance(err, HTTPException) else "Unprocessable Entity"
        return _json_error(422, msg)

    @app.errorhandler(429)
    def too_many_requests(err):
        msg = err.description if isinstance(err, HTTPException) else "Too Many Requests"
        return _json_error(429, msg)

    @app.errorhandler(Exception)
    def internal_error(err):
        if isinstance(err, HTTPException):
            return _json_error(err.code or 500, err.description or err.name)
        app.logger.exception("Unhandled exception")
        return _json_error(500, "Internal Server Error")

