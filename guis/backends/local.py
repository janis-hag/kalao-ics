import select

from PySide2.QtCore import QThread, Signal

from kalao import logs

from guis.backends.generic import GenericBackend

from kalao.definitions.enums import LogsOutputType

import config
from config import Streams


class LocalBackend(GenericBackend):
    streams_and_fps_cache = {}

    def __init__(self):
        super().__init__()

        from kalao.cacao import toolbox

        self.nuvu_stream = toolbox.open_stream_once(Streams.NUVU,
                                                    self.streams_and_fps_cache)
        self.dm_stream = toolbox.open_stream_once(Streams.DM,
                                                  self.streams_and_fps_cache)
        self.ttm_stream = toolbox.open_stream_once(Streams.TTM,
                                                   self.streams_and_fps_cache)
        self.slopes_stream = toolbox.open_stream_once(
            Streams.SLOPES, self.streams_and_fps_cache)
        self.flux_stream = toolbox.open_stream_once(Streams.FLUX,
                                                    self.streams_and_fps_cache)
        self.fli_stream = toolbox.open_stream_once(Streams.FLI,
                                                   self.streams_and_fps_cache)

        self.slopes_fps = toolbox.open_fps_once('shwfs_process-1',
                                                self.streams_and_fps_cache)
        self.nuvu_fps = toolbox.open_fps_once('nuvu_acquire-1',
                                              self.streams_and_fps_cache)
        self.bmc_fps = toolbox.open_fps_once('bmc_display-1',
                                             self.streams_and_fps_cache)

    def update(self):
        if self.nuvu_stream is not None:
            self.data.update({
                'nuvu_stream': {
                    'data': self.nuvu_stream.get_data(check=False)
                }
            })

        if self.fli_stream is not None:
            self.data.update({
                'fli_stream': {
                    'data': self.fli_stream.get_data(check=False)
                }
            })

        if self.slopes_stream is not None:
            self.data.update({
                'shwfs_slopes': {
                    'data': self.slopes_stream.get_data(check=False),
                    'tip': self.slopes_fps.get_param('slope_x'),
                    'tilt': self.slopes_fps.get_param('slope_y'),
                    'residual': self.slopes_fps.get_param('residual')
                }
            })

        if self.flux_stream is not None:
            self.data.update({
                'shwfs_slopes_flux': {
                    'data':
                        self.flux_stream.get_data(check=False),
                    'flux_avg':
                        self.slopes_fps.get_param('flux_subaperture_avg'),
                    'flux_brightest':
                        self.slopes_fps.get_param('flux_subaperture_brightest')
                }
            })

        if self.dm_stream is not None:
            self.data.update({
                'dm01disp': {
                    'data': self.dm_stream.get_data(check=False),
                    'max_stroke': self.bmc_fps.get_param('max_stroke')
                }
            })

        if self.ttm_stream is not None:
            self.data.update({
                'dm02disp': {
                    'data': self.ttm_stream.get_data(check=False)
                }
            })

        self.updated.emit()


class LocalLogsThread(QThread):
    log = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.reader = logs.get_reader(True)

        self.logs_poll = select.poll()
        self.logs_poll.register(self.reader, self.reader.get_events())

    def run(self):
        for entry in logs.seek(self.reader, LogsOutputType.QT,
                               config.GUI.initial_logs_entries):
            self.log.emit(entry)

        while self.logs_poll.poll() and not self.isInterruptionRequested():
            for entry in logs.get_last_entries(self.reader, LogsOutputType.QT):
                self.log.emit(entry)
