import argparse
from signal import SIGINT, signal

import numpy as np

from PySide6.QtCore import QMetaObject, Qt, QThread, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.main import MainWindow

import config


def handler(signal_received, frame):
    app.quit()


def cleanup():
    backend_thread.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Main GUI.')
    parser.add_argument('--engineering', action="store_false", dest="onsky",
                        help='Engineering units')
    parser.add_argument('--expert', action="store_true", dest="expert",
                        help='Expert mode')
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
    app.aboutToQuit.connect(cleanup)

    if False:
        app.setStyleSheet("""
        * {
        border: 1px solid red !important;
        }
        """)

    # Backend

    backend_thread = QThread(app)

    if args.simulation:
        import guis.backends.simulation as backends
    elif args.http:
        import guis.backends.http_client as backends
    else:
        import guis.backends.local as backends

    backend = backends.MainBackend()
    backend.moveToThread(backend_thread)

    # Timer

    streams_timer = QTimer()
    streams_timer.setInterval(int(1000 / config.GUI.refreshrate_streams))
    streams_timer.timeout.connect(backend.get_streams_all)
    # streams_timer.moveToThread(backend_thread)

    data_timer = QTimer()
    data_timer.setInterval(int(1000 / config.GUI.refreshrate_data))
    data_timer.timeout.connect(backend.get_all)
    # data_timer.moveToThread(backend_thread)

    monitoringandtelemetry_timer = QTimer()
    monitoringandtelemetry_timer.setInterval(
        int(1000 / config.GUI.refreshrate_dbs))
    monitoringandtelemetry_timer.timeout.connect(
        backend.get_monitoringandtelemetry)
    # monitoringandtelemetry_timer.moveToThread(backend_thread)

    # Windows

    unified = MainWindow(backend, streams_timer, expert_mode=args.expert,
                         on_sky_unit=args.onsky)

    backend_thread.start()

    QMetaObject.invokeMethod(backend, "get_all", Qt.QueuedConnection)
    QMetaObject.invokeMethod(backend, "get_monitoringandtelemetry",
                             Qt.QueuedConnection)

    streams_timer.start()
    data_timer.start()
    monitoringandtelemetry_timer.start()

    app.exec()
