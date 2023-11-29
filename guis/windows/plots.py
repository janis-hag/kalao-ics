from datetime import timedelta

from kalao.utils import kalao_time

from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget


class PlotsWidget(KalAOWidget):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('plots.ui', self)
        self.resize(600, 400)

        start = kalao_time.get_start_of_night_dt(kalao_time.now())

        self.start_datetimeedit.setDateTime(start)
        self.stop_datetimeedit.setDateTime(start + timedelta(hours=24))
