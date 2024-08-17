from flask import Flask, jsonify, request
from .config import Config
from .auth import Auth
from .certificate_manager import CertManager
from .server_config import ServerConfig
from .log_handler import LogHandler

app = Flask(__name__)
config = Config()
auth = Auth(config)
cert_manager = CertManager()
server_config = ServerConfig()
log_handler = LogHandler()


@app.route('/')
@auth.login_required
def index():
    return jsonify({"message": "Welcome to step-ca web UI"})


@app.route('/certificates', methods=['GET', 'POST'])
@auth.login_required
def certificates():
    if request.method == 'GET':
        return jsonify(cert_manager.list_certificates())
    elif request.method == 'POST':
        params = request.json
        return jsonify(cert_manager.generate_certificate(params))


@app.route('/certificates/<cert_id>', methods=['DELETE', 'PUT'])
@auth.login_required
def certificate_operations(cert_id):
    if request.method == 'DELETE':
        return jsonify(cert_manager.revoke_certificate(cert_id))
    elif request.method == 'PUT':
        return jsonify(cert_manager.renew_certificate(cert_id))


@app.route('/server-config', methods=['GET', 'PUT'])
@auth.login_required
def server_configuration():
    if request.method == 'GET':
        return jsonify(server_config.get_config())
    elif request.method == 'PUT':
        new_config = request.json
        return jsonify(server_config.update_config(new_config))


@app.route('/logs')
@auth.login_required
def logs():
    filter_params = request.args.to_dict()
    return jsonify(log_handler.get_logs(filter_params))


@app.route('/command-history')
@auth.login_required
def command_history():
    return jsonify(log_handler.get_command_history())


def init_app():
    # Any additional initialization can go here
    return app


if __name__ == '__main__':
    app = init_app()
    app.run(debug=True)
