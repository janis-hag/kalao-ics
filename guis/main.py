import argparse
from signal import SIGINT, signal

import numpy as np

from PySide6.QtCore import QTimer
from PySide6.QtGui import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.dm import DMWidget
from guis.windows.engineering import EngineeringWidget
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.loop_controls import LoopControlsWidget
from guis.windows.main import MainWindow
from guis.windows.monitoring import MonitoringWidget
from guis.windows.plots import PlotsWidget
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
    timer_streams = QTimer()
    timer_streams.setInterval(int(1000 / config.GUI.refreshrate_streams))
    timer_streams.timeout.connect(backend.get_streams_all)

    timer_data = QTimer()
    timer_data.setInterval(int(1000 / config.GUI.refreshrate_data))
    timer_data.timeout.connect(backend.get_all)

    timer_monitoringandtelemetry = QTimer()
    timer_monitoringandtelemetry.setInterval(
        int(1000 / config.GUI.refresharte_dbs))
    timer_monitoringandtelemetry.timeout.connect(
        backend.get_monitoringandtelemetry)

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

        loop_controls = LoopControlsWidget(backend)
        loop_controls.show()

        monitoring = MonitoringWidget(backend)
        monitoring.show()

        engineering = EngineeringWidget(backend)
        engineering.show()

        plots = PlotsWidget(backend)
        plots.show()

        logs_window = LogsWidget(backend)
        logs_window.show()

        if args.onsky:
            fli.change_units(Qt.Checked)
            slopes.change_units(Qt.Checked)
            dm.change_units(Qt.Checked)
            ttm.change_units(Qt.Checked)

    else:
        unified = MainWindow(backends, backend, timer_streams,
                             expert_mode=args.expert, on_sky_unit=args.onsky)

    timer_streams.start()
    timer_data.start()
    timer_monitoringandtelemetry.start()

    # w = FLIZoomWindow(backend, fake_data.fli_frame())

    app.exec()
