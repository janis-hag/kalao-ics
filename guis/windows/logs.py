from PySide6.QtCore import QSignalBlocker, QTimer, Signal, Slot
from PySide6.QtGui import QFontDatabase, Qt, QTextBlockUserData, QTextCursor
from PySide6.QtWidgets import QTreeWidgetItem

from kalao import database
from kalao.utils import kstring

from guis.kalao.definitions import Color
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KWidget

from kalao.definitions.enums import LogLevel

import config


class LogsData(QTextBlockUserData):
    def __init__(self, data):
        super().__init__()

        self.data = data.copy()


class LogsWidget(KWidget):
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

        #####

        self.levels_items = {}

        levels = QTreeWidgetItem(['Levels'])
        # levels.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsAutoTristate)
        # self.levels_items['toplevel'] = levels

        for level in LogLevel:
            child = QTreeWidgetItem([level.value])
            child.setCheckState(0, Qt.Checked)
            child.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            levels.addChild(child)
            self.levels_items[level.value] = child

        self.filters_tree.addTopLevelItem(levels)
        levels.setExpanded(True)

        #####

        self.services_items = {}

        services = QTreeWidgetItem(['Services'])
        # services.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsAutoTristate)
        # self.services_items['toplevel'] = services

        child = QTreeWidgetItem(['systemd'])
        child.setCheckState(0, Qt.Checked)
        child.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        services.addChild(child)
        self.services_items['systemd'] = child

        for service in sorted(config.Systemd.services.values(),
                              key=lambda x: x['unit']):
            unit = kstring.get_service_name(service['unit'])
            child = QTreeWidgetItem([unit])
            child.setCheckState(0, Qt.Checked)
            child.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            services.addChild(child)
            self.services_items[unit] = child

        self.filters_tree.addTopLevelItem(services)
        services.setExpanded(True)

        #####

        self.logs_items = {}

        logs = QTreeWidgetItem(['Logs'])
        # logs.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsAutoTristate)
        # self.logs_items['toplevel'] = logs

        child = QTreeWidgetItem(['<none>'])
        child.setCheckState(0, Qt.Checked)
        child.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        logs.addChild(child)
        self.logs_items['<none>'] = child

        for key in sorted(database.definitions['logs']['metadata'].keys()):
            key = kstring.get_log_name(key)
            child = QTreeWidgetItem([key])
            child.setCheckState(0, Qt.Checked)
            child.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            logs.addChild(child)
            self.logs_items[key] = child

        self.filters_tree.addTopLevelItem(logs)
        logs.setExpanded(True)

        #####

        entries = self.backend.get_logs_init()
        if entries is not None:
            for entry in entries:
                self.add_log_entry(entry)

        self.on_acknowledge_button_clicked(None)

        self.timer = QTimer()
        self.timer.setInterval(int(1000 / config.GUI.refreshrate_logs))
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

        if entry['level'] == LogLevel.ERROR:
            self.errors_spinbox.setValue(self.errors_spinbox.value() + 1)

            self.logged.emit(self.warnings_spinbox.value(),
                             self.errors_spinbox.value())

            style_origin = '<span class="bold red blink">'
            style_message = '<span class="bold red">'
        elif entry['level'] == LogLevel.WARNING:
            self.warnings_spinbox.setValue(self.warnings_spinbox.value() + 1)

            self.logged.emit(self.warnings_spinbox.value(),
                             self.errors_spinbox.value())

            style_message = '<span class="bold yellow">'

        message = entry["message"]
        message_splitted = entry['message'].split(' | ')
        if len(message_splitted) > 1:
            message = ' | '.join([f'{message_splitted[0]:>17s}'] +
                                 message_splitted[1:])
        else:
            message = ' '*17 + ' | ' + message

        self.logs_textedit.appendHtml(
            f'{style_timestamp}{entry["timestamp"]}{style_end} {style_origin}{entry["origin"]:>17s}{style_end}: {style_message}{message}{style_end}'
        )

        block = self.logs_textedit.document().lastBlock()
        block.setUserData(LogsData(entry))

        block.setVisible(self.entry_visible(entry))

        while self.logs_textedit.document().blockCount() > self.lines:
            cursor = QTextCursor(self.logs_textedit.document().firstBlock())
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    @Slot(QTreeWidgetItem, int)
    def on_filters_tree_itemChanged(self, item, column):
        self.filter_logs()

    @Slot(bool)
    def on_check_all_button_clicked(self, checked):
        with QSignalBlocker(self.filters_tree):
            for item in self.levels_items.values():
                item.setCheckState(0, Qt.Checked)

            for item in self.services_items.values():
                item.setCheckState(0, Qt.Checked)

            for item in self.logs_items.values():
                item.setCheckState(0, Qt.Checked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_levels_button_clicked(self, checked):
        with QSignalBlocker(self.filters_tree):
            for item in self.levels_items.values():
                item.setCheckState(0, Qt.Unchecked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_services_button_clicked(self, checked):
        with QSignalBlocker(self.filters_tree):
            for item in self.services_items.values():
                item.setCheckState(0, Qt.Unchecked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_logs_button_clicked(self, checked):
        with QSignalBlocker(self.filters_tree):
            for item in self.logs_items.values():
                item.setCheckState(0, Qt.Unchecked)

        self.filter_logs()

    def entry_visible(self, entry):
        try:
            if self.levels_items[entry['level']].checkState(0) != Qt.Checked:
                return False
        except KeyError:
            pass
            # if self.levels_items['toplevel'].checkState(0) != Qt.Checked:
            #     return False

        try:
            if self.services_items[entry['origin']].checkState(
                    0) != Qt.Checked:
                return False
        except KeyError:
            pass
            # if self.services_items['toplevel'].checkState(0) != Qt.Checked:
            #     return False

        message_splitted = entry['message'].split('|')

        if len(message_splitted) == 1:
            if self.logs_items['<none>'].checkState(0) != Qt.Checked:
                return False
        else:
            try:
                if self.logs_items[message_splitted[0].strip()].checkState(
                        0) != Qt.Checked:
                    return False
            except KeyError:
                pass
                # if self.logs_items['toplevel'].checkState(0) != Qt.Checked:
                #     return False

        return True

    def filter_logs(self):
        block = self.logs_textedit.document().begin()
        while block != self.logs_textedit.document().end():
            userdata = block.userData()
            if userdata is None:
                break

            block.setVisible(self.entry_visible(userdata.data))

            block = block.next()

        self.logs_textedit.update()

        self.logs_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logs_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.reset_scrollbars()

    @Slot(bool)
    def on_acknowledge_button_clicked(self, checked):
        self.errors_spinbox.setValue(0)
        self.warnings_spinbox.setValue(0)

        self.logged.emit(self.warnings_spinbox.value(),
                         self.errors_spinbox.value())

    def reset_scrollbars(self):
        horizontal_scrollbar = self.logs_textedit.horizontalScrollBar()
        horizontal_scrollbar.setValue(0)

        vertical_scrollbar = self.logs_textedit.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    def resizeEvent(self, event):
        self.reset_scrollbars()

        super().resizeEvent(event)
