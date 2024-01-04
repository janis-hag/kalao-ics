import time

import numpy as np

from kalao.cacao import toolbox
from kalao.utils import ktools

from PySide2.QtCore import Signal

from guis.backends.abstract import emit, timeit
from guis.backends.local import SHMFPSBackend
from guis.kalao.definitions import PokeState

import config


class AlignmentBackend(SHMFPSBackend):
    alignment_window = None

    streams_updated = Signal(object)
    streams = {}

    def __init__(self):
        super().__init__()

        self.nuvu_stream = toolbox.open_stream_once(config.Streams.NUVU,
                                                    self.streams_and_fps_cache)
        self.poke_stream = toolbox.open_stream_once(
            config.Streams.DM_REGISTRATION, self.streams_and_fps_cache)
        self.slopes_stream = toolbox.open_stream_once(
            config.Streams.SLOPES, self.streams_and_fps_cache)

        self.slopes_fps = toolbox.open_fps_once(config.FPS.SHWFS,
                                                self.streams_and_fps_cache)

    @emit('streams_updated')
    @timeit
    def get_streams_all(self):
        dm_array = np.zeros(self.poke_stream.shape, self.poke_stream.nptype)

        # Do not poke actuators
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(act)] = 0

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_stream(self.streams, config.Streams.NUVU,
                            key=f'{config.Streams.NUVU}_{PokeState.FLAT}')
        self._update_stream(self.streams, config.Streams.SHWFS,
                            key=f'{config.Streams.SHWFS}_{PokeState.FLAT}')

        self._update_param(self.streams, config.FPS.SHWFS, 'slope_x')
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_y')
        self._update_param(self.streams, config.FPS.SHWFS, 'residual')

        # Poke actuators down
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(
                act)] = -self.alignment_window.poke_amplitude

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_stream(self.streams, config.Streams.NUVU,
                            key=f'{config.Streams.NUVU}_{PokeState.DOWN}')
        self._update_stream(self.streams, config.Streams.SHWFS,
                            key=f'{config.Streams.SHWFS}_{PokeState.DOWN}')

        # Poke actuators up
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(
                act)] = self.alignment_window.poke_amplitude

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_stream(self.streams, config.Streams.NUVU,
                            key=f'{config.Streams.NUVU}_{PokeState.UP}')
        self._update_stream(self.streams, config.Streams.SHWFS,
                            key=f'{config.Streams.SHWFS}_{PokeState.UP}')

        self.streams[config.Streams.NUVU] = self.streams[
            f'{config.Streams.NUVU}_{self.alignment_window.display}']

        if self.alignment_window.display == PokeState.FLAT:
            self.streams[config.Streams.SLOPES] = self.streams[
                f'{config.Streams.SLOPES}_{PokeState.FLAT}']
        else:
            self.streams[config.Streams.SLOPES] = self.streams[
                self.alignment_window.display] - self.streams[
                    f'{config.Streams.SLOPES}_{PokeState.FLAT}']

        return self.streams
