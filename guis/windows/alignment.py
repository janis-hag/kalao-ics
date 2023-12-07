import numpy as np
from scipy import ndimage

from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QWidget

from kalao.utils import kalao_tools

from guis.kalao.definitions import HORI, VERT, Color, PokeState
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow

import config


class AlignmentSubwindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi('alignment_subwindow.ui', self)


class AlignmentWindow(KalAOMainWindow):
    def __init__(self, backend, wfs):
        super().__init__()

        self.backend = backend

        loadUi('alignment.ui', self)

        for state in PokeState:
            self.states_combobox.addItem(state, state)

        self.poke_spinbox.valueChanged.connect(self.poke_amplitude_changed)
        self.states_combobox.currentIndexChanged.connect(
            self.poke_state_changed)

        self.poke_amplitude_changed(self.poke_spinbox.value())
        self.poke_state_changed(self.states_combobox.currentIndex())

        self.actuators_to_poke = (37, 42, 97, 102)
        self.wait_after_poke = 15e-3

        pen_yellow = QPen(Color.YELLOW, 1, Qt.SolidLine, Qt.SquareCap,
                          Qt.MiterJoin)
        pen_yellow.setCosmetic(True)

        pen_blue = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap,
                        Qt.MiterJoin)
        pen_blue.setCosmetic(True)

        pen_green = QPen(Color.GREEN, 1, Qt.SolidLine, Qt.SquareCap,
                         Qt.MiterJoin)
        pen_green.setCosmetic(True)

        pen_red = QPen(Color.RED, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen_red.setCosmetic(True)

        self.subwindows = []
        for j, actuator in enumerate(self.actuators_to_poke):
            subwindow = AlignmentSubwindow()
            subwindow.subap_indexes = kalao_tools.get_subapertures_around_actuator(
                actuator)

            frame = getattr(self, f'frame_{j+1}')
            frame.layout().addWidget(subwindow, 0, 0)

            self.subwindows.append(subwindow)

            subwindow.views = []

            for i, subap in enumerate(subwindow.subap_indexes):
                wfs.rois[subap].setPen(pen_yellow)

                view = getattr(subwindow, f'view_{i + 1}')
                subwindow.views.append(view)

                view.subap = subap

                view.label = getattr(subwindow, f'label_{i+1}')

                view.lines = {
                    PokeState.FLAT: {
                        VERT: view.scene.addLine(2, 0, 2, 4, pen_blue),
                        HORI: view.scene.addLine(0, 2, 4, 2, pen_blue)
                    },
                    PokeState.UP: {
                        VERT: view.scene.addLine(2, 0, 2, 4, pen_green),
                        HORI: view.scene.addLine(0, 2, 4, 2, pen_green)
                    },
                    PokeState.DOWN: {
                        VERT: view.scene.addLine(2, 0, 2, 4, pen_red),
                        HORI: view.scene.addLine(0, 2, 4, 2, pen_red)
                    },
                }

                for j in PokeState:
                    for k in [VERT, HORI]:
                        view.lines[j][k].setZValue(1)

        backend.streams_updated.connect(self.streams_updated)

    def streams_updated(self, data):
        dxs = [0] * 4
        dys = [0] * 4
        rs = [0] * 4
        phis = [0] * 4

        for j, subwindow in enumerate(self.subwindows):
            for i, view in enumerate(subwindow.views):
                subapertures = {}
                pos = {}

                for state in PokeState:
                    frame = self.backend.consume_stream(
                        data, f'{config.FPS.NUVU}_{state}')

                    _, subapertures[
                        state] = kalao_tools.get_roi_and_subapertures(frame)

                    pos[state] = np.clip(
                        ndimage.center_of_mass(
                            subapertures[state][view.subap]), 0,
                        4) + [0.5, 0.5]
                    view.lines[state][VERT].setLine(pos[state][VERT], 0,
                                                    pos[state][VERT], 4)
                    view.lines[state][HORI].setLine(0, pos[state][HORI], 4,
                                                    pos[state][HORI])

                view.setImage(subapertures[self.display][view.subap])

                dy = 0.5 * (pos[PokeState.UP][HORI] -
                            pos[PokeState.DOWN][HORI])
                dx = -0.5 * (pos[PokeState.UP][VERT] -
                             pos[PokeState.DOWN][VERT])
                r = 0.5 * np.sqrt(dy**2 + dx**2)
                phi = np.arctan2(dy, dx) * 180 / np.pi

                view.label.updateText(r=r, phi=phi)

                dys[j] += dy
                dxs[j] += dx

        for i in range(len(dxs)):
            dxs[i] /= len(dxs)
            dys[i] /= len(dys)

            rs[i] += 0.5 * np.sqrt(dys[i]**2 + dxs[i]**2)
            phis[i] += np.arctan2(dys[i], dxs[i]) * 180 / np.pi

        self.average_label.updateText(rs=rs, phis=phis)

    def poke_state_changed(self, index):
        self.display = self.states_combobox.currentData()

    def poke_amplitude_changed(self, d):
        self.poke_amplitude = d
