from PySide6.QtCore import Signal

from kalao.interfaces import fake_data
from kalao.utils import ktools, zernike

from kalao.guis.backends.abstract import emit, timeit
from kalao.guis.backends.simulation import FakeSHMFPSBackend
from kalao.guis.utils.definitions import PokeState

import config


class AlignmentBackend(FakeSHMFPSBackend):
    alignment_window = None

    streams_all_updated = Signal(object)
    streams = {}

    @emit
    @timeit
    def streams_all(self):
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
                fake_data.wfs_frame(tiptilt=[0, 0]),
            PokeState.DOWN:
                fake_data.wfs_frame(tiptilt=[0, 0], dmdisp=data_dm_down),
            PokeState.UP:
                fake_data.wfs_frame(tiptilt=[0, 0], dmdisp=data_dm_up),
        }

        data_slopes = {
            PokeState.FLAT: fake_data.slopes(data_nuvu[PokeState.FLAT]),
            PokeState.DOWN: fake_data.slopes(data_nuvu[PokeState.DOWN]),
            PokeState.UP: fake_data.slopes(data_nuvu[PokeState.UP]),
        }

        slopes_params = fake_data.slopes_params(data_slopes[PokeState.FLAT])

        self._update_shm(self.streams, config.SHM.NUVU,
                         data_nuvu[PokeState.FLAT],
                         key=f'{config.SHM.NUVU}_{PokeState.FLAT}')
        self._update_shm(self.streams, config.SHM.NUVU,
                         data_nuvu[PokeState.UP],
                         key=f'{config.SHM.NUVU}_{PokeState.UP}')
        self._update_shm(self.streams, config.SHM.NUVU,
                         data_nuvu[PokeState.DOWN],
                         key=f'{config.SHM.NUVU}_{PokeState.DOWN}')

        self._update_shm(self.streams, config.SHM.NUVU,
                         data_nuvu[self.alignment_window.display])

        self._update_shm(self.streams, config.SHM.FLUX,
                         fake_data.flux(data_nuvu[PokeState.FLAT]))

        if self.alignment_window.display == PokeState.FLAT:
            self._update_shm(self.streams, config.SHM.SLOPES,
                             data_slopes[PokeState.FLAT])
        else:
            self._update_shm(
                self.streams, config.SHM.SLOPES,
                data_slopes[self.alignment_window.display] -
                data_slopes[PokeState.FLAT])

        self._update_fps_param(self.streams, config.FPS.SHWFS, 'slope_x_avg',
                               slopes_params['slope_x_avg'])
        self._update_fps_param(self.streams, config.FPS.SHWFS, 'slope_y_avg',
                               slopes_params['slope_y_avg'])
        self._update_fps_param(self.streams, config.FPS.SHWFS, 'residual_rms',
                               slopes_params['residual_rms'])

        return self.streams
