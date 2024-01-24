import argparse
import logging
import pickle
import traceback
from functools import partial

from flask import Flask, jsonify, make_response, request
from flask.json.provider import JSONProvider

from guis.backends.abstract import name_to_url
from guis.utils.json_coder import KalAOJSONDecoder, KalAOJSONEncoder

import config


class KalAOProvider(JSONProvider):
    encoder = KalAOJSONEncoder()
    decoder = KalAOJSONDecoder()

    def __init__(self, app):
        super().__init__(app)

    def dumps(self, obj, **kwargs):
        return self.encoder.encode(obj)

    def loads(self, obj, **kwargs):
        if isinstance(obj, bytes):
            return self.decoder.decode(obj.decode("utf-8"))
        else:
            return self.decoder.decode(obj)


app = Flask(__name__)
app.json_provider_class = KalAOProvider
app.json = KalAOProvider(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def serve(fun):
    try:
        if request.method == 'GET':
            ret = fun(backend)
        elif request.method == 'POST':
            ret = fun(backend, *tuple(request.json['args']),
                      **request.json['kwargs'])

        response_type = request.args.get('response_type', 'application/json')

        if response_type == 'application/octet-stream':
            content = pickle.dumps(ret)

            response = make_response(content)
            response.headers['Content-Length'] = len(content)
            response.headers['Content-Type'] = 'application/octet-stream'
        elif response_type == 'application/json':
            response = jsonify(ret)
        else:
            raise Exception(f'Unsupported MIME type {response_type}')

        return response
    except Exception:
        traceback.print_exc()

        return 'Internal Server Error', 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Server backend.')
    parser.add_argument('--debug', action="store_true", dest="debug",
                        help='Start Flask in debug mode')
    parser.add_argument('--simulation', action="store_true", dest="simulation",
                        help='Simulation mode')

    args = parser.parse_args()

    if args.simulation:
        import guis.backends.simulation as backends
    else:
        import guis.backends.local as backends

    for key in sorted(dir(backends.MainBackend)):
        item = getattr(backends.MainBackend, key)

        if (key.startswith('get_') or
                key.startswith('set_')) and callable(item):
            fun = partial(serve, item)
            fun.__name__ = key

            url = name_to_url(key)

            methods = ['GET', 'POST']

            if key.startswith('get_'):
                methods = ['GET']
            elif key.startswith('set_'):
                methods = ['POST']

            app.add_url_rule(url, view_func=fun, methods=methods)

            if args.debug:
                print(
                    f'Created route {url} with method(s) {", ".join(methods)}')

    global backend
    backend = backends.MainBackend()
    backend._emit = False

    app.run(host='0.0.0.0', port=config.GUI.http_port, threaded=True,
            debug=args.debug)
