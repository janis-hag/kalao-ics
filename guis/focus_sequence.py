import argparse
import signal
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.focus_sequence import FocusSequenceWindow


def sig_handler(signal_received, frame):
    app.closeAllWindows()
    app.quit()


parser = argparse.ArgumentParser(description='KalAO - Focus Sequence.')
parser.add_argument('filename', help='Focus sequence to open')

args = parser.parse_args()

signal.signal(signal.SIGINT, sig_handler)

loader = QUiLoader()

app = QApplication(['KalAO - Focus Sequence'])
app.setQuitOnLastWindowClosed(True)

QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))

# Windows

window = FocusSequenceWindow(None, file=Path(args.filename))

app.exec()
