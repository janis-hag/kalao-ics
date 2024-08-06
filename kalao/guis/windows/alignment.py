from typing import Any

import numpy as np
from scipy import ndimage

from PySide6.QtCore import Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_alignment import Ui_AlignmentWindow
from compiled.ui_alignment_subwindow import Ui_AlignmentSubwindow

from kalao.utils import ktools

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import HORI, VERT, Color, PokeState
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KMainWindow
from kalao.guis.widgets.wfs import WFSWidget

import config


class AlignmentSubwindow(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.ui = Ui_AlignmentSubwindow()
        self.ui.setupUi(self)


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

    def __init__(self, backend: AbstractBackend, wfs: WFSWidget) -> None:
        super().__init__()

        self.backend = backend

        self.ui = Ui_AlignmentWindow()
        self.ui.setupUi(self)

        for state in PokeState:
            self.ui.states_combobox.addItem(state, state)

        self.on_poke_spinbox_valueChanged(self.ui.poke_spinbox.value())
        self.on_states_combobox_currentIndexChanged(
            self.ui.states_combobox.currentIndex())

        pen_yellow = QPen(Color.YELLOW, 1, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_yellow.setCosmetic(True)

        pen_blue = QPen(Color.BLUE, 1, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_blue.setCosmetic(True)

        pen_green = QPen(Color.GREEN, 1, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_green.setCosmetic(True)

        pen_red = QPen(Color.RED, 1, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_red.setCosmetic(True)

        for subap in self.top_subaps + self.bottom_subaps + self.left_subaps + self.right_subaps:
            wfs.subapertures[subap].setPen(pen_yellow)

        self.subwindows = []
        for j, actuator in enumerate(self.actuators_to_poke):
            subwindow = AlignmentSubwindow()
            subwindow.subap_indexes = ktools.get_subapertures_around_actuator(
                actuator)

            groupbox = getattr(self.ui, f'groupbox_{j+1}')
            groupbox.layout().addWidget(subwindow, 0, 0)
            groupbox.setTitle(f'Actuator {actuator}')

            self.subwindows.append(subwindow)

            subwindow.views = []

            for i, subap in enumerate(subwindow.subap_indexes):
                wfs.subapertures[subap].setPen(pen_red)

                view = getattr(subwindow.ui, f'view_{i + 1}')
                view.updateColormap(colormaps.Grayscale())
                subwindow.views.append(view)

                view.subap = subap
                view.label = getattr(subwindow.ui, f'label_{i+1}')

                view.lines = {
                    PokeState.FLAT: {
                        VERT: view.scene().addLine(2, 0, 2, 4, pen_blue),
                        HORI: view.scene().addLine(0, 2, 4, 2, pen_blue)
                    },
                    PokeState.UP: {
                        VERT: view.scene().addLine(2, 0, 2, 4, pen_green),
                        HORI: view.scene().addLine(0, 2, 4, 2, pen_green)
                    },
                    PokeState.DOWN: {
                        VERT: view.scene().addLine(2, 0, 2, 4, pen_red),
                        HORI: view.scene().addLine(0, 2, 4, 2, pen_red)
                    },
                }

                for j in PokeState:
                    for k in [VERT, HORI]:
                        view.lines[j][k].setZValue(1)

        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
        dxs = [0] * 4
        dys = [0] * 4
        rs = [0] * 4
        phis = [0] * 4

        subapertures = {}
        for state in PokeState:
            frame = self.consume_shm(data, f'{config.SHM.NUVU}_{state}')

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

        self.ui.tb_ratio_label.updateText(tb_ratio=top_flux / bottom_flux)
        self.ui.lr_ratio_label.updateText(lr_ratio=left_flux / right_flux)

        for j, subwindow in enumerate(self.subwindows):
            for i, view in enumerate(subwindow.views):
                pos = {}

                for state in PokeState:
                    frame = self.consume_shm(data,
                                             f'{config.SHM.NUVU}_{state}',
                                             force=True)

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

        self.ui.average_label.updateText(rs=rs, phis=phis)

    @Slot(int)
    def on_states_combobox_currentIndexChanged(self, index: int) -> None:
        self.display = self.ui.states_combobox.currentData()

    @Slot(float)
    def on_poke_spinbox_valueChanged(self, d: float) -> None:
        self.poke_amplitude = d
