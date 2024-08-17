from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash


class Auth:
    def __init__(self, config):
        self.config = config

    def login_required(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth = request.authorization
            if not auth or not self.verify_credentials(auth.username, auth.password):
                return jsonify({"message": "Authentication required"}), 401
            return f(*args, **kwargs)

        return decorated_function

    def verify_credentials(self, username, password):
        stored_username = self.config.get_setting('username')
        stored_password_hash = self.config.get_setting('password_hash')
        return username == stored_username and check_password_hash(stored_password_hash, password)
