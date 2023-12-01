from PySide2.QtCore import Signal
from PySide2.QtGui import QFontDatabase, QTextCursor

from guis.backends.simulation import LogsThread
from guis.kalao.definitions import Color
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

from kalao.definitions.enums import LogType

import config


class LogsWidget(KalAOWidget):
    logged = Signal(int, int)

    lines = config.GUI.logs_lines

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('logs.ui', self)
        self.resize(600, 400)

        self.logs_textedit.setFont(
            QFontDatabase.systemFont(QFontDatabase.FixedFont))

        self.logs_textedit.document().setDefaultStyleSheet(f"""
            span {{
                white-space: pre;            
            }}
            .bold {{
                font-weight: bold;
            }}
            .red {{
                color: {Color.RED.name()};
            }}
            .yellow {{
                color: {Color.YELLOW.name()};
            }}
            .green {{
                color: {Color.GREEN.name()};
            }}
            .grey {{
                color: {Color.GREY.name()};
            }}
            .init {{
                color: {Color.GREY.name()} !important;
            }}
            .blink {{
              animation: blinker 1s linear infinite;
            }}
            @keyframes blinker {{
              50% {{
                opacity: 0;
              }}
            }}
            """)

        self.thread = LogsThread(parent=self)
        self.thread.new_log.connect(self.add_log_entry)
        self.thread.start()

        self.acknowledge_button.clicked.connect(self.acknowledge_clicked)

    def add_log_entry(self, log):
        if log is None:
            return

        if log['type'] == LogType.ERROR:
            self.errors_spinbox.setValue(self.errors_spinbox.value() + 1)

            self.logged.emit(self.errors_spinbox.value(),
                             self.warnings_spinbox.value())
        elif log['type'] == LogType.WARNING:
            self.warnings_spinbox.setValue(self.warnings_spinbox.value() + 1)

            self.logged.emit(self.errors_spinbox.value(),
                             self.warnings_spinbox.value())

        self.logs_textedit.append(log['text'])

        while self.logs_textedit.document().blockCount() > self.lines:
            cursor = QTextCursor(self.logs_textedit.document().firstBlock())
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def acknowledge_clicked(self, checked):
        self.errors_spinbox.setValue(0)
        self.warnings_spinbox.setValue(0)

        self.logged.emit(self.errors_spinbox.value(),
                         self.warnings_spinbox.value())

    def reset_scrollbars(self):
        horizontal_scrollbar = self.logs_textedit.horizontalScrollBar()
        horizontal_scrollbar.setValue(0)

        vertical_scrollbar = self.logs_textedit.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    def resizeEvent(self, event):
        self.reset_scrollbars()

        super().resizeEvent(event)
