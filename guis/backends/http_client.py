import inspect
import pickle
import traceback
from functools import partial

from PySide6.QtCore import QByteArray, QEventLoop, QUrl
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                               QNetworkRequest)

from guis.backends.abstract import AbstractBackend, name_to_url
from guis.utils.json_coder import KalAOJSONDecoder, KalAOJSONEncoder

import config


class MainBackend(AbstractBackend):
    encoder = KalAOJSONEncoder()
    decoder = KalAOJSONDecoder()

    def __init__(self):
        super().__init__()

    def __getattr__(self, path):
        return partial(self.forward, path)

    def forward(self, path, **kwargs):
        url = name_to_url(path)

        request = QNetworkRequest()
        request.setUrl(
            QUrl(
                f'http://{config.GUI.http_host}:{config.GUI.http_port}{url}?response_type={config.GUI.http_dataformat}'
            ))

        loop = QEventLoop()
        manager = QNetworkAccessManager()
        manager.finished.connect(loop.quit)

        if path.startswith('get_'):
            reply = manager.get(request)
        elif path.startswith('set_'):
            request.setHeader(QNetworkRequest.ContentTypeHeader,
                              'application/json')
            reply = manager.post(request,
                                 QByteArray(self.encoder.encode(kwargs)))

        loop.exec()

        if reply.error() != QNetworkReply.NoError:
            print(f'[ERROR] {reply.errorString()}.')
            return None

        try:
            data = reply.readAll()
            reply_type = reply.header(QNetworkRequest.ContentTypeHeader)
            if reply_type == 'application/octet-stream':
                ret = pickle.loads(data)
            elif reply_type == 'application/json':
                ret = self.decoder.decode(data.data().decode("utf-8"))
            else:
                raise Exception(f'Unsupported MIME type {reply_type}')
        except Exception:
            print(f'[ERROR] An error occurred during data loading of {url}.')
            traceback.print_exc()
            return None

        signal = path.removeprefix('set_').removeprefix('get_')
        signal = signal + '_updated'

        if signal in self.__dict__:
            self.__dict__[signal].emit(ret)

        return ret
