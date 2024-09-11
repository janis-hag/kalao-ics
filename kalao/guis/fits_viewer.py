import argparse
import signal
from pathlib import Path
from types import FrameType

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from kalao.guis.windows.fits_viewer import FITSViewerWindow


def sig_handler(signum: int, frame: FrameType | None) -> None:
    app.closeAllWindows()
    app.quit()


parser = argparse.ArgumentParser(description='KalAO - FITS viewer.')
parser.add_argument('filename', help='FITS file to open')

args = parser.parse_args()

signal.signal(signal.SIGINT, sig_handler)

app = QApplication(['KalAO - FITS viewer'])
app.setQuitOnLastWindowClosed(True)

QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))

# Windows

window = FITSViewerWindow(None, file=Path(args.filename))

app.exec()
