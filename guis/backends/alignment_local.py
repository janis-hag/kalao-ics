import time

import numpy as np

from kalao.cacao import toolbox
from kalao.utils import kalao_tools

from PySide2.QtCore import Signal

from guis.backends.abstract import AbstractBackend
from guis.kalao.definitions import PokeState

import config


class AlignmentBackend(AbstractBackend):
    alignment_window = None

    streams_updated = Signal()
    streams = {}

    def __init__(self):
        super().__init__()

        self.nuvu_stream = toolbox.open_stream_once(config.Streams.NUVU,
                                                    self.streams_and_fps_cache)
        self.poke_stream = toolbox.open_stream_once("dm01disp09",
                                                    self.streams_and_fps_cache)
        self.slopes_stream = toolbox.open_stream_once(
            config.Streams.SLOPES, self.streams_and_fps_cache)

        self.slopes_fps = toolbox.open_fps_once('shwfs_process-1',
                                                self.streams_and_fps_cache)

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update_streams(self, data):
        dm_array = np.zeros(self.poke_stream.shape, self.poke_stream.nptype)
        data_nuvu = {}
        data_slopes = {}

        # Do not poke actuators
        for act in self.alignment_window.actuators_to_poke:
            dm_array[kalao_tools.get_actuator_2d(act)] = 0

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        data_nuvu[PokeState.FLAT] = self.nuvu_stream.get_data(check=True)
        data_slopes[PokeState.FLAT] = self.slopes_stream.get_data(check=True)

        tip = self.slopes_fps.get_param('slope_x')
        tilt = self.slopes_fps.get_param('slope_y')
        residual = self.slopes_fps.get_param('residual')

        # Poke actuators down
        for act in self.alignment_window.actuators_to_poke:
            dm_array[kalao_tools.get_actuator_2d(
                act)] = -self.alignment_window.poke_amplitude

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        data_nuvu[PokeState.DOWN] = self.nuvu_stream.get_data(check=True)
        data_slopes[PokeState.DOWN] = self.slopes_stream.get_data(check=True)

        # Poke actuators up
        for act in self.alignment_window.actuators_to_poke:
            dm_array[kalao_tools.get_actuator_2d(
                act)] = self.alignment_window.poke_amplitude

        self.poke_stream.set_data(dm_array, True)
        time.sleep(self.alignment_window.wait_after_poke)
        data_nuvu[PokeState.UP] = self.nuvu_stream.get_data(check=True)
        data_slopes[PokeState.UP] = self.slopes_stream.get_data(check=True)

        data.update({
            config.Streams.NUVU: {
                'data': data_nuvu[self.alignment_window.display]
            },
            'alignment': {
                'data': data_nuvu
            }
        })

        if self.alignment_window.display == PokeState.FLAT:
            data.update({
                config.Streams.SLOPES: {
                    'data': data_slopes[PokeState.FLAT],
                    'slope_x': tip,
                    'slope_y': tilt,
                    'residual': residual
                }
            })
        else:
            data.update({
                config.Streams.SLOPES: {
                    'data':
                        data_slopes[self.alignment_window.display] -
                        data_slopes[PokeState.FLAT],
                    'slope_x':
                        tip,
                    'slope_y':
                        tilt,
                    'residual':
                        residual
                }
            })
