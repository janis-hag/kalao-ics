import numpy as np

from PySide6.QtCore import Signal

from kalao.interfaces import fake_data
from kalao.utils import ktools, zernike

from guis.backends.abstract import emit, timeit
from guis.backends.simulation import FakeSHMFPSBackend
from guis.utils.definitions import PokeState

import config


class AlignmentBackend(FakeSHMFPSBackend):
    alignment_window = None

    streams_all_updated = Signal(object)
    streams = {}

    @emit('streams_all_updated')
    @timeit
    def get_streams_all(self):
        data_dm_down = zernike.generate_pattern([0], (12, 12))
        for act in self.alignment_window.actuators_to_poke:
            data_dm_down[ktools.get_actuator_2d(
                act)] = -self.alignment_window.poke_amplitude

        data_dm_up = zernike.generate_pattern([0], (12, 12))
        for act in self.alignment_window.actuators_to_poke:
            data_dm_up[ktools.get_actuator_2d(
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
            PokeState.FLAT: fake_data.slopes(data_nuvu[PokeState.FLAT]),
            PokeState.DOWN: fake_data.slopes(data_nuvu[PokeState.DOWN]),
            PokeState.UP: fake_data.slopes(data_nuvu[PokeState.UP]),
        }

        slopes_params = fake_data.slopes_params(data_slopes[PokeState.FLAT])

        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.FLAT],
                            key=f'{config.Streams.NUVU}_{PokeState.FLAT}')
        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.UP],
                            key=f'{config.Streams.NUVU}_{PokeState.UP}')
        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[PokeState.DOWN],
                            key=f'{config.Streams.NUVU}_{PokeState.DOWN}')

        self._update_stream(self.streams, config.Streams.NUVU,
                            data_nuvu[self.alignment_window.display])

        self._update_stream(self.streams, config.Streams.FLUX,
                            fake_data.flux(data_nuvu[PokeState.FLAT]))

        if self.alignment_window.display == PokeState.FLAT:
            self._update_stream(self.streams, config.Streams.SLOPES,
                                data_slopes[PokeState.FLAT])
        else:
            self._update_stream(
                self.streams, config.Streams.SLOPES,
                data_slopes[self.alignment_window.display] -
                data_slopes[PokeState.FLAT])

        self._update_param(self.streams, config.FPS.SHWFS, 'slope_x_avg',
                           slopes_params['slope_x_avg'])
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_y_avg',
                           slopes_params['slope_y_avg'])
        self._update_param(self.streams, config.FPS.SHWFS, 'residual_rms',
                           slopes_params['residual_rms'])

        return self.streams
