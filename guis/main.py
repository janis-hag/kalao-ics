import argparse
from pathlib import Path
from signal import SIGINT, signal

import numpy as np

from PySide2.QtCore import QTimer
from PySide2.QtGui import Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication

from guis.kalao.widgets import (KalAOChart, KalAOGraphicsView, KalAOLabel,
                                KalAOSvgWidget)
from guis.windows.dm import DMWidget
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.main import MainWindow
from guis.windows.slopes import SlopesWidget
from guis.windows.ttm import TTMWidget
from guis.windows.wfs import WFSWidget

import config

##### Update functions


def clean():
    #if poke_stream is not None:
    print('Resetted DM pattern')
    #toolbox.zero_stream(poke_stream)

    unified.logs.thread.requestInterruption()
    unified.logs.thread.quit()
    unified.logs.thread.wait()


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Main GUI.')
    parser.add_argument('--split', action="store_true", dest="split",
                        help='Split windows')
    parser.add_argument('--onsky', action="store_true", dest="onsky",
                        help='On sky units')
    parser.add_argument('--max-fps', action="store", dest="fps", default=10,
                        type=int, help='Max FPS')
    parser.add_argument('--simulation', action="store_true", dest="simulation",
                        help='Simulation mode')

    args = parser.parse_args()

    signal(SIGINT, handler)

    # Numpy

    np.ma.masked_print_option.set_display('--')
    np.set_printoptions(nanstr='--')

    # Qt stuff

    loader = QUiLoader()
    loader.registerCustomWidget(KalAOLabel)
    loader.registerCustomWidget(KalAOGraphicsView)
    loader.registerCustomWidget(KalAOChart)
    loader.registerCustomWidget(KalAOSvgWidget)

    app = QApplication(['KalAO - AO tools'])
    app.setQuitOnLastWindowClosed(True)
    app.aboutToQuit.connect(clean)

    if False:
        app.setStyleSheet("""
        * {
        border: 1px solid red !important;
        }
        """)

    # Backend

    if args.simulation:
        from guis.backends.simulation import MainBackend
    else:
        from guis.backends.local import MainBackend

    backend = MainBackend()

    # Timer
    timer_images = QTimer()
    timer_images.setInterval(int(1000. / args.fps))
    timer_images.timeout.connect(backend.update)
    #timer_images.start()

    # TODO
    #timer_tiptilt = QTimer()
    #timer_tiptilt.setInterval(int(1000. / args.fps))
    #timer_tiptilt.timeout.connect(backend.update_tiptilt)
    #timer_tiptilt.start()

    # Windows

    if args.split:
        wfs = WFSWidget(backend)
        wfs.show()

        fli = FLIWidget(backend)
        fli.show()

        slopes = SlopesWidget(backend)
        slopes.show()

        flux = FluxWidget(backend)
        flux.show()

        dm = DMWidget(backend)
        dm.show()

        ttm = TTMWidget(backend)
        ttm.show()

        logs_window = LogsWidget(backend)
        logs_window.show()

        if args.onsky:
            fli.change_units(Qt.Checked)
            slopes.change_units(Qt.Checked)
            dm.change_units(Qt.Checked)
            ttm.change_units(Qt.Checked)

    else:
        unified = MainWindow(backend, timer_images)

        if args.onsky:
            unified_view.onsky_checkbox.setChecked(True)

    backend.update()

    app.exec_()

    #TODO
    #def closeEvent(self, event):
    #    if self.associated_stream is not None:
    #        stream = streams.get(self.associated_stream)
    #        if stream is not None:
    #            print(f'Closing {self.associated_stream}')
    #            #stream.close()
    #            del streams[self.associated_stream]
    #
    #    event.accept()
