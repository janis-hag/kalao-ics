import time
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QSplashScreen

from kalao.utils.rprint import rprint

# ruff: noqa: E402

loader = QUiLoader()

app = QApplication(['KalAO - AO tools'])
app.setStyle('Fusion')

QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))

pixmap = QPixmap(
    Path(__file__).absolute().parent.parent.parent /
    'logo/KalAO_logo_splash.png')
splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
splash.show()

time.sleep(0.1)  # Needed, otherwise splashscreen won't display

splash.showMessage('Starting ...', Qt.AlignHCenter | Qt.AlignBottom)
app.processEvents()


def show_message(message):
    rprint(message)
    splash.showMessage(message, Qt.AlignHCenter | Qt.AlignBottom)
    app.processEvents()


show_message('Loading libraries ...')

import argparse
import signal
import socket

import numpy as np

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QMessageBox

from kalao.guis.utils.widgets import KMessageBox
from kalao.guis.windows.main import MainWindow

import config


def sig_handler(signal_received, frame):
    app.closeAllWindows()
    app.quit()


def cleanup():
    backend_thread.quit()


parser = argparse.ArgumentParser(description='KalAO - Main GUI.')
parser.add_argument('--engineering', action='store_false', dest='onsky',
                    help='Engineering units')
parser.add_argument('--expert', action='store_true', dest='expert',
                    help='Expert mode')
parser.add_argument('--deadman', action='store_true', dest='deadman',
                    help='Deadman on')

group = parser.add_mutually_exclusive_group()
group.add_argument('--simulation', action='store_true', dest='simulation',
                   help='Simulation mode')
group.add_argument('--http', action='store_true', dest='http',
                   help='HTTP mode')

args = parser.parse_args()

signal.signal(signal.SIGINT, sig_handler)

# Numpy

np.ma.masked_print_option.set_display('--')
np.set_printoptions(nanstr='--')

# Qt stuff

app.setQuitOnLastWindowClosed(True)
app.aboutToQuit.connect(cleanup)

# Backend

show_message('Loading backend ...')

backend_thread = QThread(app)

if args.simulation:
    import kalao.guis.backends.simulation as backends
elif args.http:
    import kalao.guis.backends.http_client as backends
else:
    if socket.gethostname() != 'kalaortc01':
        print('GUI | [ERROR] Local backend can be run only on kalaortc01')
        exit(-1)

    import kalao.guis.backends.local as backends

backend = backends.MainBackend()
backend.moveToThread(backend_thread)
backend_thread.start()

# Timer

show_message('Creating timers ...')

streams_timer = QTimer()
streams_timer.setInterval(int(1000 / config.GUI.refreshrate_streams))
streams_timer.timeout.connect(backend.streams_all)
# streams_timer.moveToThread(backend_thread)

data_timer = QTimer()
data_timer.setInterval(int(1000 / config.GUI.refreshrate_data))
data_timer.timeout.connect(backend.all)
# data_timer.moveToThread(backend_thread)

monitoring_timer = QTimer()
monitoring_timer.setInterval(int(1000 / config.GUI.refreshrate_monitoring))
monitoring_timer.timeout.connect(backend.monitoring)
# monitoring_timer.moveToThread(backend_thread)

# Window

show_message('Creating main window ...')

window = MainWindow(backend, expert_mode=args.expert, on_sky_unit=args.onsky,
                    deadman=args.deadman)

if args.http:
    show_message(
        f'Trying to connect to backend (http://{config.GUI.http_host}:{config.GUI.http_port}/)'
    )

backend_version = backend.version()

if backend_version is None:
    msgbox = KMessageBox(window)
    msgbox.setIcon(QMessageBox.Critical)
    msgbox.setText('<b>Backend unreachable!</b>')
    msgbox.setInformativeText(
        f'Connection to backend seems to have failed!\nBackend URL: http://{config.GUI.http_host}:{config.GUI.http_port}/'
    )
    msgbox.setModal(True)
    msgbox.show()

elif backend_version != config.version:
    msgbox = KMessageBox(window)
    msgbox.setIcon(QMessageBox.Warning)
    msgbox.setText('<b>Different version!</b>')
    msgbox.setInformativeText(
        f'GUI version ({config.version}) differs from backend version ({backend_version}).\nUpdate your software.'
    )
    msgbox.setModal(True)
    msgbox.show()

# QTimer.singleShot(0, app, backend.streams_all)
QTimer.singleShot(0, app, backend.all)
QTimer.singleShot(0, app, backend.monitoring)

streams_timer.start()
data_timer.start()
monitoring_timer.start()

splash.finish(window)

app.exec()
