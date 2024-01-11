import numpy as np
from scipy import ndimage

from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QWidget

from kalao.utils import ktools

from guis.kalao import colormaps
from guis.kalao.definitions import HORI, VERT, Color, PokeState
from guis.kalao.mixins import BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KMainWindow

import config


class AlignmentSubwindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi('alignment_subwindow.ui', self)


class AlignmentWindow(KMainWindow, BackendDataMixin):
    actuators_to_poke = (37, 42, 97, 102)
    wait_after_poke = 15e-3

    top_subaps = [13, 14, 15, 16, 17, 18, 19]
    bottom_subaps = [101, 102, 103, 104, 105, 106, 107]
    left_subaps = [23, 34, 45, 56, 67, 78, 89]
    right_subaps = [31, 42, 53, 64, 75, 86, 97]

    top_subaps = [4, 5, 6]
    bottom_subaps = [114, 115, 116]
    left_subaps = [44, 55, 66]
    right_subaps = [54, 65, 76]

    top_subaps = [13, 4, 5, 6, 19]
    bottom_subaps = [101, 114, 115, 116, 107]
    left_subaps = [23, 44, 55, 66, 89]
    right_subaps = [31, 54, 65, 76, 97]

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

        for subap in self.top_subaps + self.bottom_subaps + self.left_subaps + self.right_subaps:
            wfs.rois[subap].setPen(pen_yellow)

        self.subwindows = []
        for j, actuator in enumerate(self.actuators_to_poke):
            subwindow = AlignmentSubwindow()
            subwindow.subap_indexes = ktools.get_subapertures_around_actuator(
                actuator)

            groupbox = getattr(self, f'groupbox_{j+1}')
            groupbox.layout().addWidget(subwindow, 0, 0)
            groupbox.setTitle(f'Actuator {actuator}')

            self.subwindows.append(subwindow)

            subwindow.views = []

            for i, subap in enumerate(subwindow.subap_indexes):
                wfs.rois[subap].setPen(pen_red)

                view = getattr(subwindow, f'view_{i + 1}')
                view.updateColormap(colormaps.Grayscale())
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

        subapertures = {}
        for state in PokeState:
            frame = self.consume_stream(data, f'{config.Streams.NUVU}_{state}')

            _, subapertures[state] = ktools.get_roi_and_subapertures(frame)

        top_flux = 0
        for subap in self.top_subaps:
            top_flux += subapertures[PokeState.FLAT][subap].sum()

        bottom_flux = 0
        for subap in self.bottom_subaps:
            bottom_flux += subapertures[PokeState.FLAT][subap].sum()

        left_flux = 0
        for subap in self.left_subaps:
            left_flux += subapertures[PokeState.FLAT][subap].sum()

        right_flux = 0
        for subap in self.bottom_subaps:
            right_flux += subapertures[PokeState.FLAT][subap].sum()

        self.tb_ratio_label.updateText(tb_ratio=top_flux / bottom_flux)
        self.lr_ratio_label.updateText(lr_ratio=left_flux / right_flux)

        for j, subwindow in enumerate(self.subwindows):
            for i, view in enumerate(subwindow.views):
                pos = {}

                for state in PokeState:
                    frame = self.consume_stream(
                        data, f'{config.Streams.NUVU}_{state}', force=True)

                    _, subapertures[state] = ktools.get_roi_and_subapertures(
                        frame)

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
