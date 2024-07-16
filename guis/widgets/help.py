from PySide6.QtCore import Slot
from PySide6.QtGui import QTextCursor, QTextDocument

from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget

import config


class HelpWidget(KWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi('help.ui', self)
        self.resize(600, 400)

        with open(config.kalao_ics_path / 'definitions/gui_help.md', 'r') as f:
            self.textedit.setMarkdown(f.read())

    @Slot(str)
    def on_search_lineedit_textEdited(self, text):
        if text == '':
            self.next_button.setEnabled(False)
            self.previous_button.setEnabled(False)
        else:
            self.next_button.setEnabled(True)
            self.previous_button.setEnabled(True)

        self._find(wrap=False, user=False)

    @Slot(bool)
    def on_next_button_clicked(self, checked):
        self._find()

    @Slot(bool)
    def on_previous_button_clicked(self, checked):
        self._find(QTextDocument.FindBackward)

    @Slot(int)
    def on_casesensitive_checkbox_stateChanged(self, state):
        self._find(wrap=False, user=False)

    @Slot(int)
    def on_wholewords_checkbox_stateChanged(self, state):
        self._find(wrap=False, user=False)

    def _find(self, flags=QTextDocument.FindFlags(), wrap=True, user=True):
        search_text = self.search_lineedit.text()

        if not user:
            self.textedit.moveCursor(QTextCursor.Left)

        if self.casesensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        if self.wholewords_checkbox.isChecked():
            flags |= QTextDocument.FindWholeWords

        direction = QTextCursor.End if flags & QTextDocument.FindBackward else QTextCursor.Start

        found = self.textedit.find(search_text, flags)

        if not found and wrap:
            self.textedit.moveCursor(direction)
            self.textedit.find(search_text, flags)
