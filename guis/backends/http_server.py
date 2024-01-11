import argparse
import pickle
import traceback
from functools import partial

from PySide6.QtCore import Signal

from flask import Flask, jsonify, make_response, request
from flask.json.provider import JSONProvider

from guis.backends.abstract import name_to_url
from guis.kalao.json_coder import (FakeSignal, KalAOJSONDecoder,
                                   KalAOJSONEncoder)

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


def serve(fun):
    try:
        if request.method == 'GET':
            ret = fun()
        elif request.method == 'POST':
            ret = fun(*tuple(request.json['args']), **request.json['kwargs'])

        if config.GUI.http_dataformat == 'pickle':
            content = pickle.dumps(ret)

            response = make_response(content)
            response.headers['Content-Length'] = len(content)
            response.headers['Content-Type'] = 'application/octet-stream'
        else:
            response = jsonify(ret)

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

    backend = backends.MainBackend()

    for key in dir(backend):
        item = getattr(backend, key)

        if isinstance(item, Signal):
            print(f'Converting signal {key}')
            setattr(backend, key, FakeSignal(key))

        elif not key.startswith('_') and callable(item):
            fun = partial(serve, item)
            fun.__name__ = key

            url = name_to_url(key)

            methods = ['GET', 'POST']

            if key.startswith('get_'):
                methods = ['GET']
            elif key.startswith('set_'):
                methods = ['POST']

            app.add_url_rule(url, view_func=fun, methods=methods)
            print(f'Created route {url} with method(s) {", ".join(methods)}')

    app.run(host='0.0.0.0', port=config.GUI.http_port, threaded=True,
            debug=args.debug)
