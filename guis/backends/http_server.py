import argparse
import pickle

from PySide6.QtCore import SignalInstance

import lz4.frame
from flask import Flask, jsonify, make_response, request
from flask.json.provider import JSONProvider

from guis.kalao.json_coder import (FakeSignal, KalAOJSONDecoder,
                                   KalAOJSONEncoder)

import config


class KalAOProvider(JSONProvider):
    def dumps(self, obj):
        return KalAOJSONEncoder().encode(obj)

    def loads(self, obj):
        if isinstance(obj, bytes):
            return KalAOJSONDecoder().decode(obj.decode("utf-8"))
        else:
            return KalAOJSONDecoder().decode(obj)


app = Flask(__name__)
app.json_provider_class = KalAOProvider
app.json = KalAOProvider(app)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    attr = getattr(backend, path, None)

    if attr is None:
        return 'Method not found', 500

    ret = attr(*tuple(request.json['args']), **request.json['kwargs'])

    content = pickle.dumps(ret)
    #content = lz4.frame.compress(pickle.dumps(ret), compression_level=3)
    response = make_response(content)
    response.headers['Content-Length'] = len(content)
    response.headers['Content-Type'] = 'application/octet-stream'
    return response


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
        attr = getattr(backend, key)

        if isinstance(attr, SignalInstance):
            setattr(backend, key, FakeSignal(key))

    app.run(host='0.0.0.0', port=config.GUI.http_port, threaded=True,
            debug=args.debug)
