import time
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from kalao.utils.rprint import rprint

from kalao.guis.utils.splashscreen import KSplashScreen

# ruff: noqa: E402

##### Start of the basic part (minimum to display splash screen)

kalao_ics_path = Path(__file__).absolute().parent.parent.parent

app = QApplication(['KalAO - AO tools'])

id = QFontDatabase.addApplicationFont(
    str(kalao_ics_path / 'assets/fonts/Inter.ttc'))
if len(QFontDatabase.applicationFontFamilies(id)) == 0:
    rprint('GUI | [WARNING] Failed to load Inter font')

QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedKingdom))

app.setStyle('Fusion')
app.setFont(QFont('Inter Display', 10))
app.setDesktopFileName('KalAO-GUI')

splashscreen = KSplashScreen(
    str(kalao_ics_path / 'assets/logo/KalAO_logo_splash.svg'),
    QFont('Inter Display', 15, QFont.Weight.Bold), QColor('#ffffff'))

splashscreen.showMessage('Starting ...')
time.sleep(0.1)  # Needed to ensure splash screen will be shown

##### End of the basic part

splashscreen.showMessage('Loading libraries ...')

import argparse
import signal
import socket
import subprocess
from types import FrameType

import numpy as np

from PySide6.QtCore import QObject, QThread, QTimer
from PySide6.QtWidgets import QMessageBox

from kalao.guis.utils.widgets import KMessageBox
from kalao.guis.windows.main import MainWindow

import config

# Monkey patch QObject to add enabled stack functionality


def setEnabledStack(self, enabled: bool, source: str) -> None:
    if not hasattr(self, '_disable_stack'):
        self._disable_stack = []

    if enabled:
        if source in self._disable_stack:
            self._disable_stack.remove(source)

        if len(self._disable_stack) == 0:
            self.setEnabled(True)
    else:
        if source not in self._disable_stack:
            self._disable_stack.append(source)

            self.setEnabled(False)


QObject.setEnabledStack = setEnabledStack

# Install .desktop (icon on wayland)


def install_desktop() -> None:
    subprocess.run('xdg-desktop-menu install assets/KalAO-GUI.desktop'.split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 16 assets/logo/ico/KalAO_icon_16.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 22 assets/logo/ico/KalAO_icon_22.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 32 assets/logo/ico/KalAO_icon_32.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 48 assets/logo/ico/KalAO_icon_48.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 64 assets/logo/ico/KalAO_icon_64.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 128 assets/logo/ico/KalAO_icon_128.png KalAO'
        .split())
    subprocess.run(
        'xdg-icon-resource install --novendor --size 256 assets/logo/ico/KalAO_icon_256.png KalAO'
        .split())


# install_desktop()

# Parse arguments


def sig_handler(signum: int, frame: FrameType | None) -> None:
    app.closeAllWindows()
    app.quit()


def cleanup() -> None:
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
signal.signal(signal.SIGTERM, sig_handler)

# Numpy

np.ma.masked_print_option.set_display('--')
np.set_printoptions(nanstr='--')

# Qt stuff

app.setQuitOnLastWindowClosed(True)
app.aboutToQuit.connect(cleanup)

# Fonts

QFontDatabase.addApplicationFont(
    str(config.kalao_ics_path / 'assets/fonts/RobotoMono-Regular.ttf'))
if len(QFontDatabase.applicationFontFamilies(id)) == 0:
    rprint('GUI | [WARNING] Failed to load RobotoMono font')

# Backend

splashscreen.showMessage('Loading backend ...')

backend_thread = QThread(app)

if args.simulation:
    import kalao.guis.backends.simulation as backends
elif args.http:
    import kalao.guis.backends.http_client as backends
else:
    if socket.gethostname() != 'kalaortc01':
        rprint('GUI | [ERROR] Local backend can only be run on kalaortc01')
        exit(-1)

    import kalao.guis.backends.local as backends

backend = backends.MainBackend()
backend.moveToThread(backend_thread)
backend_thread.start()

# Timer

splashscreen.showMessage('Creating timers ...')

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

splashscreen.showMessage('Creating window ...')

window = MainWindow(backend, expert_mode=args.expert, on_sky_unit=args.onsky,
                    deadman=args.deadman)

if args.http:
    splashscreen.showMessage(
        f'Trying to connect to backend (http://{config.GUI.http_host}:{config.GUI.http_port}/)'
    )

msgbox = None

try:
    backend_version = backend.version()
except Exception:
    backend_version = None

if backend_version is None:
    msgbox = KMessageBox(window)
    msgbox.setIcon(QMessageBox.Icon.Critical)
    msgbox.setText('<b>Backend unreachable!</b>')
    msgbox.setInformativeText(
        f'Connection to backend seems to have failed!\nBackend URL: http://{config.GUI.http_host}:{config.GUI.http_port}/'
    )
    msgbox.setModal(True)

else:
    if backend_version != config.version:
        msgbox = KMessageBox(window)
        msgbox.setIcon(QMessageBox.Icon.Warning)
        msgbox.setText('<b>Different version!</b>')
        msgbox.setInformativeText(
            f'GUI version ({config.version}) differs from backend version ({backend_version}).\nUpdate your software.'
        )
        msgbox.setModal(True)

    # QTimer.singleShot(0, backend, backend.streams_all)
    QTimer.singleShot(0, backend, backend.all)
    QTimer.singleShot(0, backend, backend.monitoring)
    QTimer.singleShot(0, backend, window.logs.get_logs_init)

    streams_timer.start()
    data_timer.start()
    monitoring_timer.start()

splashscreen.close()

window.show()
window.center()

if msgbox is not None:
    msgbox.show()

app.exec()
