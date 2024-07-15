import argparse
import inspect
import logging
import pickle
import traceback
from datetime import datetime, time, timedelta
from functools import partial

from kalao.utils import ktime, report
from kalao.utils.rprint import rprint

import pytz
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


@app.route("/night_report")
@app.route("/night_report/<night>")
def night_report(night=None):
    if night is None:
        since = ktime.get_start_of_night()
        since = since - timedelta(days=1)
    else:
        since = datetime.combine(night, time(12, 0, 0, 0))
        since = pytz.timezone('America/Santiago').localize(since)

    content = report.generate(since, since + timedelta(days=1), short=True)

    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'

    return response


def serve(fun):
    try:
        if request.method == 'GET':
            ret = fun(backend)
        elif request.method == 'POST':
            ret = fun(backend, **request.json)

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
    except Exception as e:
        string = f'URL: {request.url_rule}\nArguments: {dict(request.args)}'
        if request.is_json:
            string += f'\nJSON: {dict(request.args)}'

        rprint(''.join(traceback.format_exception(e)))
        rprint(string)

        return 'Internal Server Error', 500


if __name__ == '__main__':
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

    errors = 0

    for key, item in sorted(backends.MainBackend.__dict__.items()):
        if callable(item) and not key.startswith('_'):
            fun = partial(serve, item)
            fun.__name__ = key

            url = name_to_url(key)

            sig = inspect.signature(item)

            for i, param in enumerate(sig.parameters.values()):
                if i == 0 and param.name == 'self':
                    continue

                if param.kind != inspect.Parameter.KEYWORD_ONLY:
                    rprint(
                        f'[ERROR] Parameter {param.name} of function {key} is not keyword-only'
                    )
                    errors += 1

            if len(sig.parameters) == 1:
                methods = ['GET']
            else:
                methods = ['POST']

            app.add_url_rule(url, view_func=fun, methods=methods)

            if args.debug:
                rprint(
                    f'Created route {url} with method(s) {", ".join(methods)}')

    if errors != 0:
        rprint(f'[ERROR] {errors} errors found')
        exit()

    global backend
    backend = backends.MainBackend()

    app.run(host='0.0.0.0', port=config.GUI.http_port, threaded=True,
            debug=args.debug)
