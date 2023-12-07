import argparse
from signal import SIGINT, signal

import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.alignment import AlignmentWindow
from guis.windows.slopes import SlopesWidget
from guis.windows.wfs import WFSWidget

import config


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Alignment Tools.')
    parser.add_argument('--onsky', action="store_true", dest="onsky",
                        help='On sky units')
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

    backend.update_streams()

    # Timing - monitor fps and trigger refresh
    timer = QTimer()
    timer.setInterval(int(1000. / config.GUI.max_fps))
    timer.timeout.connect(backend.update_streams)
    timer.start()

    app.exec()
