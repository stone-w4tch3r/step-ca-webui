import uuid
from contextlib import contextmanager

from flask import Flask, request, jsonify, Response, g

from certificate_manager import CertificateManager
from shared.logger import Logger


@contextmanager
def _logging_scope():
    """
    Context manager for setting up a unique trace ID for each request in a Flask application.

    This function ensures that each request has a unique trace ID, which can be used for logging.
    It generates a unique UUID and assigns it to the Flask `g` (global) object as `trace_id`.

    Usage:
        with _logging_scope():
            # Code within this block can access g.trace_id
            pass
        # After this block, the finally part of _logging_scope is executed
    """
    g.trace_id = str(uuid.uuid4())
    try:
        yield
    finally:
        pass


class APIServer:

    def __init__(self, cert_manager: CertificateManager, logger: Logger):
        self._app = Flask(__name__)

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

    def list_certificates(self) -> Response:
        preview = request.args.get('preview', 'false').lower() == 'true'

        if preview:
            command = self.cert_manager.preview_list_certificates()
            return jsonify({"command": command})
        else:
            certificates = self.cert_manager.list_certificates()
            return jsonify(certificates)

    def generate_certificate(self) -> Response:
        params = request.json  # TODO explicit flask params
        preview = request.args.get('preview', 'false').lower() == 'true'

        if preview:
            command = self.cert_manager.preview_generate_certificate(params)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.generate_certificate(params)
            return jsonify(result)

    def renew_certificate(self) -> Response:
        cert_id = request.args.get('certId')
        duration = int(request.args.get('duration'))
        preview = request.args.get('preview', 'false').lower() == 'true'

        if preview:
            command = self.cert_manager.preview_renew_certificate(cert_id, duration)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.renew_certificate(cert_id, duration)
            return jsonify(result)

    def revoke_certificate(self) -> Response:
        cert_id = request.args.get('certId')
        preview = request.args.get('preview', 'false').lower() == 'true'

        if preview:
            command = self.cert_manager.preview_revoke_certificate(cert_id)
            return jsonify({"command": command})
        else:
            result = self.cert_manager.revoke_certificate(cert_id)
            return jsonify(result)

    def get_logs(self) -> Response:
        filters = {
            'severity': request.args.getlist('severity'),
            'traceId': request.args.get('traceId'),
            'commands_only': request.args.get('commandsOnly', 'false').lower() == 'true',
            'page': int(request.args.get('page', 1)),
            'pageSize': int(request.args.get('pageSize', 20))
        }
        logs = self.logger.get_logs(filters)
        return jsonify(logs)

    def get_log_entry(self) -> Response | tuple[Response, int]:
        log_id = int(request.args.get('logId'))
        log_entry = self.logger.get_log_entry(log_id)
        if log_entry:
            return jsonify(log_entry)
        else:
            return jsonify({"error": "Log entry not found"}), 404
