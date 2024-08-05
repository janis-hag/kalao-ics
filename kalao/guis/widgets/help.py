from PySide6.QtCore import Slot
from PySide6.QtGui import Qt, QTextCursor, QTextDocument
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

        with open(config.kalao_ics_path / 'definitions/gui_help.md', 'r') as f:
            self.ui.textedit.setMarkdown(f.read())

    @Slot(str)
    def on_search_lineedit_textEdited(self, text: str) -> None:
        if text == '':
            self.ui.next_button.setEnabled(False)
            self.ui.previous_button.setEnabled(False)
        else:
            self.ui.next_button.setEnabled(True)
            self.ui.previous_button.setEnabled(True)

        self._find(wrap=False, user=False)

    @Slot(bool)
    def on_next_button_clicked(self, checked: bool) -> None:
        self._find()

    @Slot(bool)
    def on_previous_button_clicked(self, checked: bool) -> None:
        self._find(QTextDocument.FindFlag.FindBackward)

    @Slot(int)
    def on_casesensitive_checkbox_stateChanged(self,
                                               state: Qt.CheckState) -> None:
        self._find(wrap=False, user=False)

    @Slot(int)
    def on_wholewords_checkbox_stateChanged(self,
                                            state: Qt.CheckState) -> None:
        self._find(wrap=False, user=False)

    def _find(self, flags: QTextDocument.FindFlag = QTextDocument.FindFlag(0),
              wrap: bool = True, user: bool = True) -> None:
        search_text = self.ui.search_lineedit.text()

        if not user:
            self.ui.textedit.moveCursor(QTextCursor.MoveOperation.Left)

        if self.ui.casesensitive_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self.ui.wholewords_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords

        direction = QTextCursor.MoveOperation.End if flags & QTextDocument.FindFlag.FindBackward else QTextCursor.MoveOperation.Start

        found = self.ui.textedit.find(search_text, flags)

        if not found and wrap:
            self.ui.textedit.moveCursor(direction)
            self.ui.textedit.find(search_text, flags)
