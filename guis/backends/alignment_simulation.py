import numpy as np

from PySide6.QtCore import Signal

from kalao.interfaces import fake_data
from kalao.utils import kalao_tools

from guis.backends.abstract import AbstractBackend
from guis.kalao.definitions import PokeState

import config

#TODO: replace with Streams enum?


class AlignmentBackend(AbstractBackend):
    alignment_window = None

    streams_updated = Signal()
    streams = {}

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update_streams(self, data):
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
                    'data': data_slopes[PokeState.FLAT]
                }
            })
        else:
            data.update({
                config.Streams.SLOPES: {
                    'data':
                        data_slopes[self.alignment_window.display] -
                        data_slopes[PokeState.FLAT]
                }
            })
        data[config.Streams.SLOPES].update(
            fake_data.slopes_params(data[config.Streams.SLOPES]['data']))
