from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget


class HelpWidget(KWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi('help.ui', self)
        self.resize(600, 400)