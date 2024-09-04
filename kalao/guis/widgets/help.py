from PySide6.QtWidgets import QWidget

from compiled.ui_help import Ui_HelpWidget

from kalao.guis.utils.widgets import KWidget

import config


class HelpWidget(KWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.ui = Ui_HelpWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.find_widget.setup(self.ui.help_textedit)

        with open(config.kalao_ics_path / 'definitions/gui_help.md', 'r') as f:
            self.ui.help_textedit.setMarkdown(f.read())
