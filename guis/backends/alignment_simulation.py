import numpy as np

from kalao.interfaces import fake_data
from kalao.utils import kalao_tools

from guis.backends.generic import GenericBackend
from guis.kalao.definitions import PokeState

#TODO: replace with Streams enum?


class AlignmentSimulationBackend(GenericBackend):
    alignment_window = None

    def update(self):
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

        self.data.update({
            'nuvu_stream': {
                'data': data_nuvu[self.alignment_window.display]
            },
            'alignment': {
                'data': data_nuvu
            }
        })

        if self.alignment_window.display == PokeState.FLAT:
            self.data.update({
                'shwfs_slopes': {
                    'data': data_slopes[PokeState.FLAT]
                }
            })
        else:
            self.data.update({
                'shwfs_slopes': {
                    'data':
                        data_slopes[self.alignment_window.display] -
                        data_slopes[PokeState.FLAT]
                }
            })
        self.data['shwfs_slopes'].update(
            fake_data.slopes_params(self.data['shwfs_slopes']['data']))

        self.updated.emit()
