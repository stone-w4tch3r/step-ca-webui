import uuid
from contextlib import contextmanager

from flasgger import Swagger, swag_from
from flask import Flask, request, jsonify, Response, g

from certificate_manager import CertificateManager
from shared.logger import Logger


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

        self._swagger = self._setup_swagger()
        self.cert_manager = cert_manager
        self.logger = logger

        self._app.add_url_rule('/certificates', 'list_certificates', self.list_certificates, methods=['GET'])
        self._app.add_url_rule('/certificates/generate', 'generate_certificate', self.generate_certificate, methods=['POST'])
        self._app.add_url_rule('/certificates/renew', 'renew_certificate', self.renew_certificate, methods=['POST'])
        self._app.add_url_rule('/certificates/revoke', 'revoke_certificate', self.revoke_certificate, methods=['POST'])
        self._app.add_url_rule('/logs', 'get_logs', self.get_logs, methods=['GET'])
        self._app.add_url_rule('/logs/single', 'get_log_entry', self.get_log_entry, methods=['GET'])

        @self._app.before_request
        def set_logging_scope():
            g.logging_scope = _logging_scope()
            g.logging_scope.__enter__()

        @self._app.after_request
        def clear_logging_scope(response):
            if hasattr(g, 'logging_scope'):
                g.logging_scope.__exit__(None, None, None)
            return response

    def run(self):
        self._app.run(host='0.0.0.0', port=5000)

    # TODO specify type in response
    @swag_from()
    def list_certificates(self) -> Response:
        preview = request.args['preview']

        # TODO: validate here

        if preview:
            command = self.cert_manager.preview_list_certificates()
            return jsonify({"command": command})
        else:
            certificates = self.cert_manager.list_certificates()
            return jsonify(certificates)

    # TODO specify type in response
    @swag_from()
    def generate_certificate(self) -> Response:
        preview = request.args['preview']
        key_name = request.json['keyName']
        key_type = request.json['keyType']
        duration = request.json['duration']

        # TODO: validate here

        if preview:
            command = self.cert_manager.preview_generate_certificate(key_name, key_type, duration)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.generate_certificate(key_name, key_type, duration)
            return jsonify(result)

    # TODO specify type in response
    @swag_from()
    def renew_certificate(self) -> Response:
        cert_id = request.args['certId']
        duration = request.args['duration']
        preview = request.args['preview']

        # TODO: validate here

        if preview:
            command = self.cert_manager.preview_renew_certificate(cert_id, duration)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.renew_certificate(cert_id, duration)
            return jsonify(result)

    # TODO specify type in response
    @swag_from()
    def revoke_certificate(self) -> Response:
        cert_id = request.args['certId']
        preview = request.args['preview']

        # TODO: validate here

        if preview:
            command = self.cert_manager.preview_revoke_certificate(cert_id)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.revoke_certificate(cert_id)
            return jsonify(result)

    # TODO specify type in response
    @swag_from()
    def get_logs(self) -> Response:
        severity = request.args['severity']
        trace_id = request.args['traceId']
        commands_only = request.args['commandsOnly']
        page = request.args['page']
        page_size = request.args['pageSize']

        # TODO: validate here

        filters = {
            'severity': severity,
            'traceId': trace_id,
            'commands_only': commands_only,
            'page': page,
            'pageSize': page_size
        }
        logs = self.logger.get_logs(filters)
        return jsonify(logs)

    # TODO specify type in response
    @swag_from()
    def get_log_entry(self) -> Response | tuple[Response, int]:
        log_id = request.args['logId']

        # TODO: validate here

        log_entry = self.logger.get_log_entry(int(log_id))
        if log_entry:
            return jsonify(log_entry)
        else:
            return jsonify({"error": "Log entry not found"}), 404

    def _setup_swagger(self):
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

        return Swagger(self._app, config=config, template_file="../docs/core-api.yaml")  # TODO package in DOCKERFILE
