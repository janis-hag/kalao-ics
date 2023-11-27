import argparse
import time
from pathlib import Path
from signal import SIGINT, signal

import numpy as np
from scipy import ndimage

from PySide2.QtCore import QTimer
from PySide2.QtGui import QPen, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget

from kalao.cacao import toolbox
from kalao.interfaces import fake_data
from kalao.utils import kalao_tools

from kalao_gui import SlopesWindow, Streams, WFSWindow, clean, streams

from guis.lib.kalao_widgets import (Color, KalAOChart, KalAOGraphicsView,
                                    KalAOLabel)
from guis.lib.ui_loader import loadUi

from kalao.definitions.enums import StrEnum

ui_path = Path(__file__).absolute().parent


class PokeState(StrEnum):
    FLAT = "No poke"
    DOWN = "Poke down"
    UP = "Poke up"


HORI = 0
VERT = 1


class AlignmentSubwindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/alignment_subwindow.ui', self)


class AlignmentWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/alignment.ui', self)

        for state in PokeState:
            self.states_combobox.addItem(state)

        self.poke_spinbox.valueChanged.connect(self.poke_amplitude_changed)
        self.states_combobox.currentIndexChanged.connect(
            self.poke_state_changed)

        #self.actuators_to_poke = (50, 53, 86, 89)
        self.actuators_to_poke = (37, 42, 97, 102)
        self.wait_after_poke = 15e-3

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
                view.margins = (0.1, 0.1, 0.1, 0.1)
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

    def update_data(self, frames):
        dxs = [0] * 4
        dys = [0] * 4
        rs = [0] * 4
        phis = [0] * 4

        for j, subwindow in enumerate(self.subwindows):
            for i, view in enumerate(subwindow.views):
                subapertures = {}
                pos = {}

                for state in PokeState:
                    _, subapertures[
                        state] = kalao_tools.get_roi_and_subapertures(
                            frames[state])

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
        self.display = PokeState(self.states_combobox.currentText())

    def poke_amplitude_changed(self, d):
        self.poke_amplitude = d


def update():
    dm_array = np.zeros(poke_stream.shape, poke_stream.nptype)
    data_nuvu = {}
    data_slopes = {}

    # Do not poke actuators
    for act in alignment.actuators_to_poke:
        dm_array[kalao_tools.get_actuator_2d(act)] = 0

    poke_stream.set_data(dm_array, True)
    time.sleep(alignment.wait_after_poke)
    data_nuvu[PokeState.FLAT] = nuvu_stream.get_data(check=True)
    data_slopes[PokeState.FLAT] = slopes_stream.get_data(check=True)

    tip = slopes_fps.get_param('slope_x')
    tilt = slopes_fps.get_param('slope_y')
    residual = slopes_fps.get_param('residual')

    # Poke actuators down
    for act in alignment.actuators_to_poke:
        dm_array[kalao_tools.get_actuator_2d(act)] = -alignment.poke_amplitude

    poke_stream.set_data(dm_array, True)
    time.sleep(alignment.wait_after_poke)
    data_nuvu[PokeState.DOWN] = nuvu_stream.get_data(check=True)
    data_slopes[PokeState.DOWN] = slopes_stream.get_data(check=True)

    # Poke actuators up
    for act in alignment.actuators_to_poke:
        dm_array[kalao_tools.get_actuator_2d(act)] = alignment.poke_amplitude

    poke_stream.set_data(dm_array, True)
    time.sleep(alignment.wait_after_poke)
    data_nuvu[PokeState.UP] = nuvu_stream.get_data(check=True)
    data_slopes[PokeState.UP] = slopes_stream.get_data(check=True)

    alignment.update_data(data_nuvu)
    wfs.update_data(data_nuvu[alignment.display])
    if alignment.display == PokeState.FLAT:
        slopes.update_data(data_slopes[alignment.display], tip, tilt, residual)
    else:
        slopes.update_data(
            data_slopes[alignment.display] - data_slopes[PokeState.FLAT], tip,
            tilt, residual)


def update_fake():
    data_dm_down = np.zeros((12, 12))
    for act in alignment.actuators_to_poke:
        data_dm_down[kalao_tools.get_actuator_2d(
            act)] = -alignment.poke_amplitude

    data_dm_up = np.zeros((12, 12))
    for act in alignment.actuators_to_poke:
        data_dm_up[kalao_tools.get_actuator_2d(act)] = alignment.poke_amplitude

    data_dm = {
        PokeState.FLAT: np.zeros((12, 12)),
        PokeState.DOWN: data_dm_down,
        PokeState.UP: data_dm_up,
    }

    data_nuvu = {
        PokeState.FLAT:
            fake_data.nuvu_frame(tiptilt=[0, 0]),
        PokeState.DOWN:
            fake_data.nuvu_frame(tiptilt=[0, 0], dmdisp=data_dm_down),
        PokeState.UP:
            fake_data.nuvu_frame(tiptilt=[0, 0], dmdisp=data_dm_up),
    }

    data_slopes = {
        PokeState.FLAT: fake_data.slopes(data_nuvu[PokeState.FLAT]).filled(),
        PokeState.DOWN: fake_data.slopes(data_nuvu[PokeState.DOWN]).filled(),
        PokeState.UP: fake_data.slopes(data_nuvu[PokeState.UP]).filled(),
    }

    slopes_data = data_slopes[PokeState.FLAT]
    slopes_tip = slopes_data[0:11, 0:11]
    slopes_tilt = slopes_data[0:11, 11:22]
    tip = np.mean(slopes_tip)
    tilt = np.mean(slopes_tilt)
    residual = np.sqrt(np.mean(tip**2 + tilt**2))

    alignment.update_data(data_nuvu)
    wfs.update_data(data_nuvu[alignment.display])
    if alignment.display == PokeState.FLAT:
        slopes.update_data(data_slopes[alignment.display], tip, tilt, residual)
    else:
        slopes.update_data(
            data_slopes[alignment.display] - data_slopes[PokeState.FLAT], tip,
            tilt, residual)


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='KalAO - Tool to align the WFS and the DM.')
    parser.add_argument('--onsky', action="store_true", dest="onsky",
                        help='On sky units')
    parser.add_argument('--max-fps', action="store", dest="fps", default=10,
                        type=int, help='Max FPS')
    parser.add_argument('--test', action="store_true", dest="test",
                        help='Test')

    args = parser.parse_args()

    signal(SIGINT, handler)

    ##### Qt stuff

    loader = QUiLoader()
    loader.registerCustomWidget(KalAOLabel)
    loader.registerCustomWidget(KalAOGraphicsView)
    loader.registerCustomWidget(KalAOChart)

    app = QApplication(['KalAO - Alignment tools'])
    app.setQuitOnLastWindowClosed(True)
    app.aboutToQuit.connect(clean)

    ##### Open needed streams

    if not args.test:
        nuvu_stream = toolbox.open_stream_once(Streams.NUVU, streams)
        poke_stream = toolbox.open_stream_once("dm01disp09", streams)
        dm_stream = toolbox.open_stream_once(Streams.DM, streams)
        ttm_stream = toolbox.open_stream_once(Streams.TTM, streams)
        slopes_stream = toolbox.open_stream_once(Streams.SLOPES, streams)
        flux_stream = toolbox.open_stream_once(Streams.FLUX, streams)
        fli_stream = toolbox.open_stream_once(Streams.FLI, streams)

        slopes_fps = toolbox.open_fps_once('shwfs_process-1', streams)
        nuvu_fps = toolbox.open_fps_once('nuvu_acquire-1', streams)
        bmc_fps = toolbox.open_fps_once('bmc_display-1', streams)

    ##### Windows

    update_fun = update

    if Streams.NUVU in streams or args.test:
        wfs = WFSWindow()
        wfs.show()

    if Streams.SLOPES in streams or args.test:
        slopes = SlopesWindow()
        slopes.show()

    alignment = AlignmentWindow()
    alignment.show()

    if args.test:
        update_fun = update_fake

    update_fun()

    # Timing - monitor fps and trigger refresh
    timer = QTimer()
    timer.setInterval(int(1000. / args.fps))
    timer.timeout.connect(update_fun)
    timer.start()

    app.exec_()
