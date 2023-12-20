from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtGui import QFontDatabase, Qt, QTextBlockUserData, QTextCursor

from guis.kalao.definitions import Color
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

from kalao.definitions.enums import LogType

import config


class LogsData(QTextBlockUserData):
    def __init__(self, data):
        super().__init__()

        data = data.copy()

        if 'text' in data:
            del data['text']

        self.data = data


class LogsWidget(KalAOWidget):
    logged = Signal(int, int)

    lines = config.GUI.logs_lines

    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.filter_type_combobox.addItem("All", "All")
        for type in LogType:
            self.filter_type_combobox.addItem(type.name, type.value)

        self.filter_origin_combobox.addItem("All", "All")
        self.filter_origin_combobox.addItem("systemd", "systemd")
        for service in config.Systemd.services.values():
            unit = service['unit'].removeprefix('kalao_').removesuffix(
                '.service')
            self.filter_origin_combobox.addItem(unit, unit)

        entries = self.backend.get_logs_init()
        if entries is not None:
            for entry in entries:
                self.add_log_entry(entry)

        self.on_acknowledge_button_clicked(None)

        self.timer = QTimer()
        self.timer.setInterval(int(1000. / config.GUI.refreshrate_logs))
        self.timer.timeout.connect(self.get_logs_new)
        self.timer.start()

    def get_logs_new(self):
        entries = self.backend.get_logs_new()
        if entries is not None:
            for entry in entries:
                self.add_log_entry(entry)

    def add_log_entry(self, entry):
        if entry is None:
            return

        style_timestamp = '<span class="grey">'
        style_origin = '<span>'
        style_message = '<span>'
        style_end = '</span>'

        if entry['type'] == LogType.ERROR:
            self.errors_spinbox.setValue(self.errors_spinbox.value() + 1)

            self.logged.emit(self.errors_spinbox.value(),
                             self.warnings_spinbox.value())

            style_origin = '<span class="bold red">'
            style_message = '<span class="bold red">'
        elif entry['type'] == LogType.WARNING:
            self.warnings_spinbox.setValue(self.warnings_spinbox.value() + 1)

            self.logged.emit(self.errors_spinbox.value(),
                             self.warnings_spinbox.value())

            style_message = '<span class="bold yellow">'

        self.logs_textedit.appendHtml(
            f'{style_timestamp}{entry["timestamp"]}{style_end} {style_origin}{entry["origin"]:>15s}{style_end}: {style_message}{entry["message"]}{style_end}'
        )

        block = self.logs_textedit.document().lastBlock()
        block.setUserData(LogsData(entry))

        block.setVisible(self.log_visible(entry))

        while self.logs_textedit.document().blockCount() > self.lines:
            cursor = QTextCursor(self.logs_textedit.document().firstBlock())
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    @Slot(int)
    def on_filter_origin_combobox_currentIndexChanged(self, index):
        self.filter_logs()

    @Slot(int)
    def on_filter_type_combobox_currentIndexChanged(self, index):
        self.filter_logs()

    def log_visible(self, log):
        if self.filter_type_combobox.currentData() not in [log['type'], "All"]:
            return False

        if self.filter_origin_combobox.currentData() not in [
                log['origin'], "All"
        ]:
            return False

        return True

    def filter_logs(self):
        block = self.logs_textedit.document().begin()
        while block != self.logs_textedit.document().end():
            userdata = block.userData()
            if userdata is None:
                break

            block.setVisible(self.log_visible(userdata.data))

            block = block.next()

        self.logs_textedit.update()

        self.logs_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logs_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.reset_scrollbars()

    @Slot(bool)
    def on_acknowledge_button_clicked(self, checked):
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
