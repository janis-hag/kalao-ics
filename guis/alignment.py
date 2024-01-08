import argparse
from signal import SIGINT, signal

import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.widgets.slopes import SlopesWidget
from guis.widgets.wfs import WFSWidget
from guis.windows.alignment import AlignmentWindow

import config


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Alignment Tools.')
    parser.add_argument('--simulation', action="store_true", dest="simulation",
                        help='Simulation mode')

    args = parser.parse_args()

    signal(SIGINT, handler)

    # Numpy

    np.ma.masked_print_option.set_display('--')
    np.set_printoptions(nanstr='--')

    # Qt stuff

    loader = QUiLoader()

    app = QApplication(['KalAO - Alignment tools'])
    app.setQuitOnLastWindowClosed(True)

    # Windows

    if args.simulation:
        from guis.backends.alignment_simulation import AlignmentBackend
    else:
        from guis.backends.alignment_local import AlignmentBackend

    backend = AlignmentBackend()

    wfs = WFSWidget(backend)
    wfs.show()

    slopes = SlopesWidget(backend)
    slopes.show()

    alignment = AlignmentWindow(backend, wfs)
    alignment.show()

    backend.alignment_window = alignment

    timer = QTimer()
    timer.setInterval(int(1000 / config.GUI.refreshrate_streams))
    timer.timeout.connect(backend.get_streams_all)
    timer.start()

    app.exec()
