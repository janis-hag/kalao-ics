import numpy as np

from PySide6.QtCore import Signal

from kalao.interfaces import fake_data
from kalao.utils import kalao_tools

from guis.backends.abstract import emit, timeit
from guis.backends.simulation import FakeSHMFPSBackend
from guis.kalao.definitions import PokeState

import config


class AlignmentBackend(FakeSHMFPSBackend):
    alignment_window = None

    streams_updated = Signal(object)
    streams = {}

    @emit('streams_updated')
    @timeit
    def get_streams_all(self):
        data_dm_down = np.zeros((12, 12))
        for act in self.alignment_window.actuators_to_poke:
            data_dm_down[kalao_tools.get_actuator_2d(
                act)] = -self.alignment_window.poke_amplitude

        data_dm_up = np.zeros((12, 12))
        for act in self.alignment_window.actuators_to_poke:
            data_dm_up[kalao_tools.get_actuator_2d(
                act)] = self.alignment_window.poke_amplitude

        data_nuvu = {
            PokeState.FLAT:
                fake_data.nuvu_frame(tiptilt=[0, 0]),
            PokeState.DOWN:
                fake_data.nuvu_frame(tiptilt=[0, 0], dmdisp=data_dm_down),
            PokeState.UP:
                fake_data.nuvu_frame(tiptilt=[0, 0], dmdisp=data_dm_up),
        }

        data_slopes = {
            PokeState.FLAT:
                fake_data.slopes(data_nuvu[PokeState.FLAT]).filled(),
            PokeState.DOWN:
                fake_data.slopes(data_nuvu[PokeState.DOWN]).filled(),
            PokeState.UP:
                fake_data.slopes(data_nuvu[PokeState.UP]).filled(),
        }

        slopes_params = fake_data.slopes_params(data_slopes[PokeState.FLAT])

        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.FLAT],
                            key=f'{config.FPS.NUVU}_{PokeState.FLAT}')
        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.UP],
                            key=f'{config.FPS.NUVU}_{PokeState.UP}')
        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.DOWN],
                            key=f'{config.FPS.NUVU}_{PokeState.DOWN}')

        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[self.alignment_window.display])

        if self.alignment_window.display == PokeState.FLAT:
            self._update_stream(self.streams, config.Streams.SLOPES,
                                data_slopes[PokeState.FLAT])
        else:
            self._update_stream(
                self.streams, config.Streams.SLOPES,
                data_slopes[self.alignment_window.display] -
                data_slopes[PokeState.FLAT])

        self._update_params(self.streams, config.FPS.SHWFS, 'slope_x',
                            slopes_params['slope_x'])
        self._update_params(self.streams, config.FPS.SHWFS, 'slope_y',
                            slopes_params['slope_y'])
        self._update_params(self.streams, config.FPS.SHWFS, 'residual',
                            slopes_params['residual'])

        return self.streams
