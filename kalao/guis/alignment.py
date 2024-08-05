import argparse
import signal
from types import FrameType

import numpy as np

from PySide6.QtCore import QLocale, QTimer
from PySide6.QtWidgets import QApplication

from kalao.guis.utils import colormaps
from kalao.guis.widgets.flux import FluxWidget
from kalao.guis.widgets.slopes import SlopesWidget
from kalao.guis.widgets.wfs import WFSWidget
from kalao.guis.windows.alignment import AlignmentWindow

import config


def sig_handler(signum: int, frame: FrameType | None) -> None:
    app.closeAllWindows()
    app.quit()


parser = argparse.ArgumentParser(description='KalAO - Alignment Tools.')
parser.add_argument('--simulation', action='store_true', dest='simulation',
                    help='Simulation mode')

args = parser.parse_args()

signal.signal(signal.SIGINT, sig_handler)

# Numpy

np.ma.masked_print_option.set_display('--')
np.set_printoptions(nanstr='--')

# Qt stuff

app = QApplication(['KalAO - Alignment tools'])
app.setQuitOnLastWindowClosed(True)

QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))

# Windows

if args.simulation:
    from kalao.guis.backends.alignment_simulation import AlignmentBackend
else:
    from kalao.guis.backends.alignment_local import AlignmentBackend

backend = AlignmentBackend()

wfs = WFSWidget(backend)
wfs.show()
wfs.ui.wfs_view.updateColormap(colormaps.Grayscale())

slopes = SlopesWidget(backend)
slopes.show()
slopes.ui.slopes_view.updateColormap(colormaps.GrayscaleTransparent())

flux = FluxWidget(backend)
flux.show()
flux.ui.flux_view.updateColormap(colormaps.GrayscaleTransparent())

alignment = AlignmentWindow(backend, wfs)
alignment.show()

backend.alignment_window = alignment

timer = QTimer()
timer.setInterval(int(1000 / config.GUI.refreshrate_streams))
timer.timeout.connect(backend.streams_all)
timer.start()

app.exec()
