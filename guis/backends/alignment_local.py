import time

import numpy as np

from PySide6.QtCore import Signal

from kalao.cacao import toolbox
from kalao.utils import ktools

from guis.backends.abstract import emit, timeit
from guis.backends.local import SHMFPSBackend
from guis.utils.definitions import PokeState

import config


class AlignmentBackend(SHMFPSBackend):
    alignment_window = None

    streams_all_updated = Signal(object)
    streams = {}

    def __init__(self):
        super().__init__()

        self.nuvu_shm = toolbox.get_shm(config.SHM.NUVU)
        self.poke_shm = toolbox.get_shm(config.SHM.DM_REGISTRATION)
        self.slopes_shm = toolbox.get_shm(config.SHM.SLOPES)

        self.slopes_fps = toolbox.get_fps(config.FPS.SHWFS)

    @emit
    @timeit
    def streams_all(self):
        dm_array = np.zeros(self.poke_shm.shape, self.poke_shm.nptype)

        # Do not poke actuators
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(act)] = 0

        self.poke_shm.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_shm(self.streams, config.SHM.NUVU,
                         key=f'{config.SHM.NUVU}_{PokeState.FLAT}')
        self._update_shm(self.streams, config.SHM.SLOPES,
                         key=f'{config.SHM.SLOPES}_{PokeState.FLAT}')

        self._update_shm(self.streams, config.SHM.FLUX)

        self._update_fps_param(self.streams, config.FPS.SHWFS, 'slope_x_avg')
        self._update_fps_param(self.streams, config.FPS.SHWFS, 'slope_y_avg')
        self._update_fps_param(self.streams, config.FPS.SHWFS, 'residual_rms')

        # Poke actuators down
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(
                act)] = -self.alignment_window.poke_amplitude

        self.poke_shm.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_shm(self.streams, config.SHM.NUVU,
                         key=f'{config.SHM.NUVU}_{PokeState.DOWN}')
        self._update_shm(self.streams, config.SHM.SLOPES,
                         key=f'{config.SHM.SLOPES}_{PokeState.DOWN}')

        # Poke actuators up
        for act in self.alignment_window.actuators_to_poke:
            dm_array[ktools.get_actuator_2d(
                act)] = self.alignment_window.poke_amplitude

        self.poke_shm.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        self._update_shm(self.streams, config.SHM.NUVU,
                         key=f'{config.SHM.NUVU}_{PokeState.UP}')
        self._update_shm(self.streams, config.SHM.SLOPES,
                         key=f'{config.SHM.SLOPES}_{PokeState.UP}')

        self.streams[config.SHM.NUVU] = self.streams[
            f'{config.SHM.NUVU}_{self.alignment_window.display}']

        if self.alignment_window.display == PokeState.FLAT:
            self.streams[config.SHM.SLOPES] = self.streams[
                f'{config.SHM.SLOPES}_{PokeState.FLAT}']
        else:
            self.streams[config.SHM.SLOPES] = self.streams[
                self.alignment_window.display] - self.streams[
                    f'{config.SHM.SLOPES}_{PokeState.FLAT}']

        return self.streams
