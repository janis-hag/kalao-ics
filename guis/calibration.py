from signal import SIGINT, signal

import numpy as np

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication

from guis.windows.calibration import CalibrationWindow


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    signal(SIGINT, handler)

    # Numpy
    np.ma.masked_print_option.set_display('--')
    np.set_printoptions(nanstr='--')

    loader = QUiLoader()

    app = QApplication(['KalAO - Calibration tools'])
    app.setQuitOnLastWindowClosed(True)

    dm = CalibrationWindow('dm', 1, (11, 22), (12, 12))
    ttm = CalibrationWindow('ttm', 2, (12, 12), (1, 2))

    app.exec()
