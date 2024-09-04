import functools
import pickle
from typing import Any

from PySide6.QtCore import QByteArray, QEventLoop, QUrl
from PySide6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                               QNetworkRequest)

from kalao.common.json import KalAOJSONDecoder, KalAOJSONEncoder
from kalao.common.rprint import rprint

from kalao.guis.backends.abstract import AbstractBackend, name_to_url

import config


class MainBackend(AbstractBackend):
    encoder = KalAOJSONEncoder()
    decoder = KalAOJSONDecoder()

    def __init__(self) -> None:
        super().__init__()

        for key, item in sorted(vars(AbstractBackend).items()):
            if callable(item) and not key.startswith('_') and not key.endswith(
                    '_updated') and key != 'name':
                func = functools.partial(self._forward, key)
                func.__name__ = key

                self.__dict__[key] = func

    def name(self) -> str:
        return 'remote'

    def _forward(self, path: str, **kwargs: Any) -> Any:
        url = name_to_url(path)

        request = QNetworkRequest()
        request.setUrl(
            QUrl(f'http://{config.GUI.http_host}:{config.GUI.http_port}{url}'))
        request.setRawHeader(b'Accept', config.GUI.http_dataformat.encode())

        if path == 'version':
            request.setTransferTimeout(
                int(config.GUI.http_request_timeout * 1000))

        loop = QEventLoop()
        manager = QNetworkAccessManager()
        manager.finished.connect(loop.quit)

        if len(kwargs) == 0:
            reply = manager.get(request)
        else:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,
                              'application/json')
            reply = manager.post(
                request, QByteArray(self.encoder.encode(kwargs).encode()))

        # loop.exec(QEventLoop.ExcludeUserInputEvents)
        loop.exec()

        if reply.error() != QNetworkReply.NetworkError.NoError:
            rprint(f'[ERROR] {reply.errorString()}.')
            raise Exception(f'[ERROR] {reply.errorString()}.')

        data = reply.readAll()
        reply_type = reply.header(
            QNetworkRequest.KnownHeaders.ContentTypeHeader)
        if reply_type == 'application/octet-stream':
            ret = pickle.loads(data.data())
        elif reply_type == 'application/json':
            ret = self.decoder.decode(data.data().decode('utf-8'))
        else:
            raise Exception(f'Unsupported MIME type {reply_type}')

        signal = path + '_updated'

        if signal in self.__dict__:
            self.__dict__[signal].emit(ret)

        return ret
