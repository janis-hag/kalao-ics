import pickle
import traceback
from functools import partial

from PySide6.QtCore import QByteArray, QEventLoop, QUrl, Signal
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                               QNetworkRequest)

from guis.backends.abstract import AbstractBackend, name_to_url
from guis.kalao.json_coder import (FakeSignal, KalAOJSONDecoder,
                                   KalAOJSONEncoder)

import config


class MainBackend(AbstractBackend):
    encoder = KalAOJSONEncoder()
    decoder = KalAOJSONDecoder()

    def __init__(self):
        super().__init__()

    def __getattr__(self, path):
        if '_updated' in path:
            self.add_signal(path)
            return getattr(self, path)
        else:
            return partial(self.forward, path)

    def add_signal(self, name):
        cls = self.__class__

        new_cls = type(
            cls.__name__,
            cls.__bases__,
            {
                **cls.__dict__, name: Signal(object)
            },
        )

        self.__class__ = new_cls

    def forward(self, path, *args, **kwargs):
        url = name_to_url(path)

        request = QNetworkRequest()
        request.setUrl(QUrl(f"http://localhost:{config.GUI.http_port}{url}"))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/json")

        data = {
            'args': list(args),
            'kwargs': kwargs,
        }

        manager = QNetworkAccessManager()

        if path.startswith('get_'):
            reply = manager.get(request)
        elif path.startswith('set_'):
            reply = manager.post(request,
                                 QByteArray(self.encoder.encode(data)))

        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()

        if reply.error() != QNetworkReply.NoError:
            print(f'[ERROR] {reply.errorString()}.')
            return None

        try:
            data = reply.readAll()
            if config.GUI.http_dataformat == 'pickle':
                ret = pickle.loads(data)
            else:
                ret = self.decoder.decode(data.data().decode("utf-8"))
        except Exception:
            print(f'[ERROR] An error occurred during data loading of {url}.')
            traceback.print_exc()
            return None

        if isinstance(ret, FakeSignal):
            return getattr(self, ret.name).emit(*ret.args)

        return ret
