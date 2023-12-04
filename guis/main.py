import argparse
from signal import SIGINT, signal

import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtGui import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.dm import DMWidget
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.main import MainWindow
from guis.windows.slopes import SlopesWidget
from guis.windows.ttm import TTMWidget
from guis.windows.wfs import WFSWidget

import config


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Main GUI.')
    parser.add_argument('--split', action="store_true", dest="split",
                        help='Split windows')
    parser.add_argument('--onsky', action="store_true", dest="onsky",
                        help='On sky units')
    parser.add_argument('--simulation', action="store_true", dest="simulation",
                        help='Simulation mode')
    parser.add_argument('--http', action="store_true", dest="http",
                        help='HTTP mode')

    args = parser.parse_args()

    signal(SIGINT, handler)

    # Numpy

    np.ma.masked_print_option.set_display('--')
    np.set_printoptions(nanstr='--')

    # Qt stuff
    loader = QUiLoader()

    app = QApplication(['KalAO - AO tools'])
    app.setQuitOnLastWindowClosed(True)

    if False:
        app.setStyleSheet("""
        * {
        border: 1px solid red !important;
        }
        """)

    # Backend
    if args.simulation:
        import guis.backends.simulation as backends
    elif args.http:
        import guis.backends.http_client as backends
    else:
        import guis.backends.local as backends

    backend = backends.MainBackend()

    # Timer
    timer_images = QTimer()
    timer_images.setInterval(int(1000. / config.GUI.max_fps))
    timer_images.timeout.connect(backend.update_streams)

    timer_tiptilt = QTimer()
    timer_tiptilt.setInterval(int(1000. / config.GUI.max_fps))
    timer_tiptilt.timeout.connect(backend.update_tiptilt)

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
        unified = MainWindow(backends, backend, timer_images)

        if args.onsky:
            unified_view.onsky_checkbox.setChecked(True)

    timer_images.start()
    timer_tiptilt.start()

    app.exec()

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
