import select

import numpy as np

from PySide6.QtCore import QThread, Signal

from kalao import logs
from kalao.cacao import aocontrol, toolbox
from kalao.utils import database

from guis.backends.abstract import AbstractBackend

from kalao.definitions.enums import LogsOutputType

import config
from config import Streams


class SHMFPSBackend(AbstractBackend):
    streams_and_fps_cache = {}

    def _update_stream(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name,
                                          self.streams_and_fps_cache)

        if stream is None:
            return

        cnt0 = stream.IMAGE.md.cnt0

        if data.get(stream_name, {}).get('cnt0') == cnt0:
            data.update({stream_name: {'data': None, }})
        else:
            data.update({
                stream_name: {
                    'updated': True,
                    'cnt0': cnt0,
                    'data': stream.get_data(check=False),
                }
            })

    def _update_params(self, data, fps_name, param_name):
        fps = toolbox.open_fps_once(fps_name, self.streams_and_fps_cache)

        if fps is None:
            return

        param = fps.get_param(param_name)

        if data.get(fps_name) is None:
            data[fps_name] = {}

        if data.get(fps_name, {}).get(param_name, {}).get('cnt0') != param:
            data[fps_name].update({
                param_name: {
                    'updated': True,
                    'cnt0': param,
                    'value': param
                }
            })


class MainBackend(SHMFPSBackend):
    streams_updated = Signal()
    streams = {}

    tiptilt_updated = Signal()
    tiptilt = {}

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update_streams(self, data):
        self._update_stream(data, config.Streams.DM)
        self._update_params(data, config.FPS.BMC, 'max_stroke')

        self._update_stream(data, config.Streams.NUVU)

        self._update_stream(data, config.Streams.SLOPES)
        self._update_params(data, config.FPS.SHWFS, 'slope_x')
        self._update_params(data, config.FPS.SHWFS, 'slope_y')
        self._update_params(data, config.FPS.SHWFS, 'residual')

        self._update_stream(data, config.Streams.FLUX)
        self._update_params(data, config.FPS.SHWFS, 'flux_subaperture_avg')
        self._update_params(data, config.FPS.SHWFS,
                            'flux_subaperture_brightest')

        self._update_stream(data, config.Streams.FLI)

        self._update_stream(data, 'aol1_mgainfact')

    @AbstractBackend.timeit('tiptilt', 'tiptilt_updated')
    def update_tiptilt(self, data):
        self._update_stream(data, config.Streams.TTM)

    def get_plots_data(self, dt_start, dt_end, monitoring_keys,
                       telemetry_keys):

        data = {}

        if len(monitoring_keys) > 0:
            data['monitoring'] = database.read_mongo_to_pandas_by_timestamp(
                'monitoring', dt_start, dt_end, monitoring_keys)

        if len(telemetry_keys) > 0:
            data['telemetry'] = database.read_mongo_to_pandas_by_timestamp(
                'telemetry', dt_start, dt_end, telemetry_keys)

        return data


class DMChannelsBackend(SHMFPSBackend):
    streams_updated = Signal()
    streams = {}

    def __init__(self, dm_number):
        super().__init__()

        self.dm_number = dm_number

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update_data(self, data):
        self._update_stream(data, f'dm{self.dm_number:02d}disp')

        for i in range(0, 12):
            self._update_stream(data, f'dm{self.dm_number:02d}disp{i:02d}')

    def reset_dm(self, dm_number):
        aocontrol.reset_dm(dm_number)

    def reset_channel(self, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)


class LogsThread(QThread):
    new_log = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.reader = logs.get_reader(True)

        self.logs_poll = select.poll()
        self.logs_poll.register(self.reader, self.reader.get_events())

    def run(self):
        for entry in logs.seek(self.reader, LogsOutputType.QT,
                               config.GUI.initial_logs_entries):
            entry['text'] = '<span class="init">' + entry['text'] + '<span>'
            self.new_log.emit(entry)

        while self.logs_poll.poll() and not self.isInterruptionRequested():
            for entry in logs.get_last_entries(self.reader, LogsOutputType.QT):
                self.new_log.emit(entry)
