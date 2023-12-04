import pickle
from functools import partial

from PySide6.QtCore import QByteArray, QEventLoop, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

import lz4.frame

from guis.backends.abstract import AbstractBackend
from guis.kalao.json_coder import FakeSignal, KalAOJSONEncoder

import config


class MainBackend(AbstractBackend):
    def __init__(self):
        super().__init__()

        self.manager = QNetworkAccessManager(self)

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
        request = QNetworkRequest()
        request.setUrl(QUrl(f"http://localhost:{config.GUI.http_port}/{path}"))
        request.setHeader(QNetworkRequest.ContentTypeHeader,
                          "application/json")

        data = {
            'args': list(args),
            'kwargs': kwargs,
        }

        reply = self.manager.post(request,
                                  QByteArray(KalAOJSONEncoder().encode(data)))

        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()

        #reply.error()
        data = reply.readAll()
        #data = lz4.frame.decompress(data.data())
        ret = pickle.loads(data)  #.toStdString())

        if isinstance(ret, FakeSignal):
            return getattr(self, ret.name).emit(*ret.args)

        return ret
