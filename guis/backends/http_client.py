import pickle
import traceback
from functools import partial

from PySide6.QtCore import QByteArray, QEventLoop, QUrl
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                               QNetworkRequest)

from kalao.utils.json import KalAOJSONDecoder, KalAOJSONEncoder
from kalao.utils.rprint import rprint

from guis.backends.abstract import AbstractBackend, name_to_url

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

        if len(kwargs) == 0:
            reply = manager.get(request)
        else:
            request.setHeader(QNetworkRequest.ContentTypeHeader,
                              'application/json')
            reply = manager.post(request,
                                 QByteArray(self.encoder.encode(kwargs)))

        loop.exec()

        if reply.error() != QNetworkReply.NoError:
            rprint(f'[ERROR] {reply.errorString()}.')
            return None

        try:
            data = reply.readAll()
            reply_type = reply.header(QNetworkRequest.ContentTypeHeader)
            if reply_type == 'application/octet-stream':
                ret = pickle.loads(data)
            elif reply_type == 'application/json':
                ret = self.decoder.decode(data.data().decode('utf-8'))
            else:
                raise Exception(f'Unsupported MIME type {reply_type}')
        except Exception as e:
            rprint(f'[ERROR] An error occurred during data loading of {url}.')
            rprint(''.join(traceback.format_exception(e)))
            return None

        signal = path + '_updated'

        if signal in self.__dict__:
            self.__dict__[signal].emit(ret)

        return ret
