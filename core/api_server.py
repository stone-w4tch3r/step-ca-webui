import sys
import traceback
import uuid
from contextlib import contextmanager
from typing import Any

from flasgger import Swagger, swag_from
from flask import Flask, request, jsonify, Response, g, abort, make_response

from certificate_manager import CertificateManager
from shared.logger import Logger
from shared.models import LogSeverity, KeyType


@contextmanager
def _logging_scope():
    """
    Context manager for setting up a unique trace ID for each request in a Flask application.
    """
    g.trace_id = str(uuid.uuid4())
    try:
        yield
    finally:
        pass


class APIServer:

    def __init__(self, cert_manager: CertificateManager, logger: Logger):
        self._app = Flask(__name__)

        self._cert_manager = cert_manager
        self._logger = logger

        _Setuper.setup_swagger(self)
        _Setuper.setup_routes(self)
        _Setuper.setup_handlers(self)

    def run(self):
        self._app.run(host='0.0.0.0', port=5000)

    @swag_from()
    def list_certificates(self) -> Response:
        preview = _Helper.ensure_bool(request.json['preview'] if 'preview' in request.json else None)

        if preview:
            command = self._cert_manager.preview_list_certificates()
            return jsonify({"command": command})
        else:
            certificates = self._cert_manager.list_certificates()
            return jsonify(certificates)

    @swag_from()
    def generate_certificate(self) -> tuple[Response, int] | Response:
        preview = _Helper.ensure_bool(request.args.get('preview'))
        key_name = _Helper.ensure_str(request.json['keyName'] if 'keyName' in request.json else None)
        key_type = _Helper.ensure_key_type(request.json['keyType'] if 'keyType' in request.json else None)
        duration = _Helper.ensure_positive_int(request.json['duration'] if 'duration' in request.json else None)

        if preview:
            command = self._cert_manager.preview_generate_certificate(key_name, key_type, duration)
            return jsonify({"command": command})
        else:
            result = self._cert_manager.generate_certificate(key_name, key_type, duration)
            return jsonify(result)

    @swag_from()
    def renew_certificate(self) -> tuple[Response, int] | Response:
        preview = _Helper.ensure_bool(request.json['preview'] if 'preview' in request.json else None)
        cert_id = _Helper.ensure_str(request.json['certId'] if 'certId' in request.json else None)
        duration = _Helper.ensure_positive_int(request.json['duration'] if 'duration' in request.json else None)

        if preview:
            command = self._cert_manager.preview_renew_certificate(cert_id, duration)
            return jsonify({"command": command})
        else:
            result = self._cert_manager.renew_certificate(cert_id, duration)
            return jsonify(result)

    @swag_from()
    def revoke_certificate(self) -> tuple[Response, int] | Response:
        preview = _Helper.ensure_bool(request.json['preview'] if 'preview' in request.json else None)
        cert_id = _Helper.ensure_str(request.json['certId'] if 'certId' in request.json else None)

        if preview:
            command = self._cert_manager.preview_revoke_certificate(cert_id)
            return jsonify({"command": command})
        else:
            result = self._cert_manager.revoke_certificate(cert_id)
            return jsonify(result)

    @swag_from()
    def get_logs(self) -> Response:
        severity = _Helper.ensure_severity_list(request.json['severity'] if 'severity' in request.json else None)
        trace_id = _Helper.ensure_uuid(request.json['traceId'] if 'traceId' in request.json else None)
        commands_only = _Helper.ensure_bool(request.json['commandsOnly'] if 'commandsOnly' in request.json else None)
        page = _Helper.ensure_positive_int(request.json['page'] if 'page' in request.json else None)
        page_size = _Helper.ensure_positive_int(request.json['pageSize'] if 'pageSize' in request.json else None)

        filters = {
            'severity': severity,
            'traceId': trace_id,
            'commands_only': commands_only,
            'page': page,
            'pageSize': page_size
        }
        logs = self._logger.get_logs(filters)
        return jsonify(logs)

    @swag_from()
    def get_log_entry(self) -> tuple[Response, int] | Response:
        log_id = request.args.get('logId', type=_Helper.ensure_positive_int)

        log_entry = self._logger.get_log_entry(int(log_id))
        if not log_entry:
            return _Helper.create_plaintext_response("Log entry not found"), 404
        return jsonify(log_entry)


# noinspection PyProtectedMember
class _Setuper:
    @staticmethod
    def setup_routes(api: APIServer) -> None:
        api._app.add_url_rule('/certificates', 'list_certificates', api.list_certificates, methods=['GET'])
        api._app.add_url_rule('/certificates/generate', 'generate_certificate', api.generate_certificate, methods=['POST'])
        api._app.add_url_rule('/certificates/renew', 'renew_certificate', api.renew_certificate, methods=['POST'])
        api._app.add_url_rule('/certificates/revoke', 'revoke_certificate', api.revoke_certificate, methods=['POST'])
        api._app.add_url_rule('/logs', 'get_logs', api.get_logs, methods=['POST'])
        api._app.add_url_rule('/logs/single', 'get_log_entry', api.get_log_entry, methods=['GET'])

    @staticmethod
    def setup_swagger(api: APIServer) -> Swagger:
        config = {
            "headers": [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', "GET, POST"),
            ],
            "specs": [
                {
                    "endpoint": 'apispec_1',
                    "route": '/apispec_1.json',
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/apidocs/",
            "openapi": "3.0.0",
        }

        return Swagger(api._app, config=config, template_file="../docs/core-api.yaml")  # TODO package in DOCKERFILE

    @staticmethod
    def setup_handlers(api: APIServer) -> None:
        @api._app.before_request
        def set_logging_scope():
            g.logging_scope = _logging_scope()
            g.logging_scope.__enter__()

        @api._app.after_request
        def clear_logging_scope(response):
            if hasattr(g, 'logging_scope'):
                g.logging_scope.__exit__(None, None, None)
            return response

        @api._app.errorhandler(400)
        def custom_400(error):
            response = _Helper.create_plaintext_response(error.description)
            response.status_code = 400
            return response

        @api._app.errorhandler(500)
        def custom_500(_):
            trace_id = g.trace_id if hasattr(g, 'trace_id') else "UNKNOWN"

            response = _Helper.create_plaintext_response(f"Internal server error, trace_id [{trace_id}]")
            response.status_code = 500
            return response

        @api._app.errorhandler(Exception)
        def handle_all_exceptions(_):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            formatted_exception = traceback.format_exception(exc_type, exc_value, exc_traceback)
            e_info = ''.join(formatted_exception)

            trace_id = g.trace_id if hasattr(g, 'trace_id') else uuid.UUID("00000000-0000-0000-0000-000000000000")
            message = f"Unhandled exception, trace_id [{trace_id}]:\n\n\n{e_info}"
            api._logger.log_scoped(LogSeverity.ERROR, message)

            response = _Helper.create_plaintext_response(message)
            response.status_code = 500
            return response


class _Helper:
    @staticmethod
    def ensure_severity_list(inpt: Any) -> list[str]:
        allowed_severities = [s.upper() for s in LogSeverity]
        if not isinstance(inpt, list):
            abort(400, f"Invalid severity list, must be a list, got: {type(inpt)}")
        for value in inpt:
            if value not in allowed_severities:
                abort(400, f"Invalid severity: '{value}', must be one of {allowed_severities}")
        return inpt

    @staticmethod
    def ensure_key_type(inpt: Any) -> str:
        allowed_key_types = [k.upper() for k in KeyType]
        if inpt not in allowed_key_types:
            abort(400, f"Invalid key type: '{inpt}', must be one of {allowed_key_types}")
        return inpt

    @staticmethod
    def ensure_uuid(inpt: Any) -> uuid.UUID:
        try:
            result = uuid.UUID(inpt)
        except Exception:
            abort(400, f"Invalid UUID: '{inpt}' of type {type(inpt)}")
        return result

    @staticmethod
    def ensure_positive_int(inpt: Any) -> int:
        if not isinstance(inpt, int) or inpt <= 0:
            abort(400, f"Invalid value: '{inpt}' of type {type(inpt)}, must be a positive integer")
        return int(inpt)

    @staticmethod
    def ensure_bool(inpt: Any) -> bool:
        try:
            return bool(inpt)
        except Exception:
            abort(400, f"Invalid value: '{inpt}' of type {type(inpt)}, must be a boolean")

    @staticmethod
    def ensure_str(inpt: Any) -> str:
        if not isinstance(inpt, str):
            abort(400, f"Invalid value: '{inpt}' of type {type(inpt)}, must be a string")
        return inpt

    @staticmethod
    def create_plaintext_response(content: str) -> Response:
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain'
        return response
