from datetime import timezone

import numpy as np

from PySide6.QtCore import QDateTime, QSignalBlocker, QTimer, Signal, Slot
from PySide6.QtGui import (QCursor, QFont, QGuiApplication, QResizeEvent, Qt,
                           QTextBlockUserData, QTextCursor)
from PySide6.QtWidgets import QTreeWidgetItem, QWidget

from compiled.ui_logs import Ui_LogsWidget

from kalao import database
from kalao.utils import kstring

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import ascii2html
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendActionMixin
from kalao.guis.utils.widgets import KWidget

from kalao.definitions.dataclasses import LogEntry
from kalao.definitions.enums import LogLevel

import config


class LogsData(QTextBlockUserData):
    def __init__(self, data: LogEntry) -> None:
        super().__init__()

        self.data = data


class LogsWidget(KWidget, BackendActionMixin):
    logged = Signal(int, int)

    max_entries = config.GUI.logs_max_entries

    last_cursor = None

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_LogsWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.logs_textedit.setFont(QFont('Roboto Mono'))

        self.ui.logs_textedit.document().setDefaultStyleSheet(
            ascii2html.stylesheet + f"""
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
        # levels.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsAutoTristate)
        # self.levels_items['toplevel'] = levels

        for level in LogLevel:
            child = QTreeWidgetItem([level.value])
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                           Qt.ItemFlag.ItemIsEnabled)
            levels.addChild(child)
            self.levels_items[level.value] = child

        self.ui.filters_tree.addTopLevelItem(levels)
        levels.setExpanded(True)

        #####

        self.services_items = {}

        services = QTreeWidgetItem(['Services'])
        # services.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsAutoTristate)
        # self.services_items['toplevel'] = services

        child = QTreeWidgetItem(['systemd'])
        child.setCheckState(0, Qt.CheckState.Checked)
        child.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                       Qt.ItemFlag.ItemIsEnabled)
        services.addChild(child)
        self.services_items['systemd'] = child

        for service in sorted(config.Systemd.services.values(),
                              key=lambda service: service['unit']):
            unit = kstring.get_service_name(service['unit'])
            child = QTreeWidgetItem([unit])
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                           Qt.ItemFlag.ItemIsEnabled)
            services.addChild(child)
            self.services_items[unit] = child

        self.ui.filters_tree.addTopLevelItem(services)
        services.setExpanded(True)

        #####

        self.logs_items = {}

        logs = QTreeWidgetItem(['Logs'])
        # logs.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsAutoTristate)
        # self.logs_items['toplevel'] = logs

        child = QTreeWidgetItem(['<none>'])
        child.setCheckState(0, Qt.CheckState.Checked)
        child.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                       Qt.ItemFlag.ItemIsEnabled)
        logs.addChild(child)
        self.logs_items['<none>'] = child

        for key in sorted(database.definitions['logs']['metadata'].keys()):
            key = kstring.get_log_name(key)
            child = QTreeWidgetItem([key])
            child.setCheckState(0, Qt.CheckState.Checked)
            child.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                           Qt.ItemFlag.ItemIsEnabled)
            logs.addChild(child)
            self.logs_items[key] = child

        self.ui.filters_tree.addTopLevelItem(logs)
        logs.setExpanded(True)

        #####

        until = QDateTime.currentDateTime()
        since = until.addSecs(-3600)

        self.ui.since_datetimeedit.setDateTime(since)
        self.ui.until_datetimeedit.setDateTime(until)

        self.logs_timer = QTimer(parent=self)
        self.logs_timer.setInterval(int(1000 / config.GUI.refreshrate_logs))
        self.logs_timer.timeout.connect(self.get_logs_new)

    def get_logs_init(self) -> None:
        entries = self.action_send([
            self.ui.retrieve_button, self.ui.live_button
        ], self.backend.logs, lines=config.GUI.logs_initial_entries)

        for entry in entries:
            self.add_log_entry(entry)

        self.on_acknowledge_button_clicked(False)

        self.logs_timer.start()

    def get_logs_new(self) -> None:
        entries = self.action_send([], self.backend.logs,
                                   cursor=self.last_cursor)

        for entry in entries:
            self.add_log_entry(entry)

    def add_log_entry(self, entry: LogEntry) -> None:
        if entry is None:
            return

        style_timestamp = '<span class="grey">'
        style_origin = '<span>'
        style_message = '<span>'
        style_end = '</span>'

        if entry.level == LogLevel.ERROR:
            self.ui.errors_spinbox.setValue(self.ui.errors_spinbox.value() + 1)

            self.logged.emit(self.ui.warnings_spinbox.value(),
                             self.ui.errors_spinbox.value())

            style_origin = '<span class="bold red">'
            style_message = '<span class="bold red">'
        elif entry.level == LogLevel.WARNING:
            self.ui.warnings_spinbox.setValue(
                self.ui.warnings_spinbox.value() + 1)

            self.logged.emit(self.ui.warnings_spinbox.value(),
                             self.ui.errors_spinbox.value())

            style_origin = '<span class="bold yellow">'
            style_message = '<span class="bold yellow">'

        message_splitted = entry.message.split(' | ', 1)
        if len(message_splitted) == 1:
            message = f'{" "*17} | {message_splitted[0]}'
        else:
            message = f'{message_splitted[0]:>17s} | {message_splitted[1]}'

        self.ui.logs_textedit.appendHtml(
            f'{style_timestamp}{entry.timestamp.astimezone():%y-%m-%d %H:%M:%S}{style_end} {style_origin}{entry.origin:>17s}{style_end}: {style_message}{ascii2html.translate(message)}{style_end}'
        )

        block = self.ui.logs_textedit.document().lastBlock()
        block.setUserData(LogsData(entry))

        block.setVisible(self.entry_visible(entry))

        while self.ui.logs_textedit.document().blockCount() > self.max_entries:
            cursor = QTextCursor(self.ui.logs_textedit.document().firstBlock())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        self.last_cursor = entry.cursor

    @Slot(QDateTime)
    def on_since_datetimeedit_dateTimeChanged(self,
                                              datetime: QDateTime) -> None:
        self.ui.until_datetimeedit.setMinimumDateTime(datetime)

    @Slot(QDateTime)
    def on_until_datetimeedit_dateTimeChanged(self,
                                              datetime: QDateTime) -> None:
        self.ui.since_datetimeedit.setMaximumDateTime(datetime)

    @Slot(bool)
    def on_retrieve_button_clicked(self, checked: bool) -> None:
        # Set cursor as display can be long
        QGuiApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))

        since = self.ui.since_datetimeedit.dateTime().toUTC().toPython(
        ).replace(tzinfo=timezone.utc)
        until = self.ui.until_datetimeedit.dateTime().toUTC().toPython(
        ).replace(tzinfo=timezone.utc)

        self.logs_timer.stop()

        entries = self.action_send([
            self.ui.retrieve_button, self.ui.live_button
        ], self.backend.logs_between, since=since, until=until)

        self.ui.logs_textedit.clear()

        self.max_entries = np.inf

        if entries is not None:
            for entry in entries:
                self.add_log_entry(entry)

        self.on_acknowledge_button_clicked(False)

        QGuiApplication.restoreOverrideCursor()

    @Slot(bool)
    def on_live_button_clicked(self, checked: bool) -> None:
        self.ui.logs_textedit.clear()

        self.max_entries = config.GUI.logs_max_entries

        self.get_logs_init()

    @Slot(QTreeWidgetItem, int)
    def on_filters_tree_itemChanged(self, item: QTreeWidgetItem,
                                    column: int) -> None:
        self.filter_logs()

    @Slot(bool)
    def on_check_all_button_clicked(self, checked: bool) -> None:
        with QSignalBlocker(self.ui.filters_tree):
            for item in self.levels_items.values():
                item.setCheckState(0, Qt.CheckState.Checked)

            for item in self.services_items.values():
                item.setCheckState(0, Qt.CheckState.Checked)

            for item in self.logs_items.values():
                item.setCheckState(0, Qt.CheckState.Checked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_levels_button_clicked(self, checked: bool) -> None:
        with QSignalBlocker(self.ui.filters_tree):
            for item in self.levels_items.values():
                item.setCheckState(0, Qt.CheckState.Unchecked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_services_button_clicked(self, checked: bool) -> None:
        with QSignalBlocker(self.ui.filters_tree):
            for item in self.services_items.values():
                item.setCheckState(0, Qt.CheckState.Unchecked)

        self.filter_logs()

    @Slot(bool)
    def on_clear_logs_button_clicked(self, checked: bool) -> None:
        with QSignalBlocker(self.ui.filters_tree):
            for item in self.logs_items.values():
                item.setCheckState(0, Qt.CheckState.Unchecked)

        self.filter_logs()

    def entry_visible(self, entry: LogEntry) -> bool:
        try:
            if self.levels_items[entry.level].checkState(
                    0) != Qt.CheckState.Checked:
                return False
        except KeyError:
            pass
            # if self.levels_items['toplevel'].checkState(0) != Qt.CheckState.Checked:
            #     return False

        try:
            if self.services_items[entry.origin].checkState(
                    0) != Qt.CheckState.Checked:
                return False
        except KeyError:
            pass
            # if self.services_items['toplevel'].checkState(0) != Qt.CheckState.Checked:
            #     return False

        message_splitted = entry.message.split(' | ', 1)

        if len(message_splitted) == 1:
            if self.logs_items['<none>'].checkState(
                    0) != Qt.CheckState.Checked:
                return False
        else:
            try:
                if self.logs_items[message_splitted[0].strip()].checkState(
                        0) != Qt.CheckState.Checked:
                    return False
            except KeyError:
                pass
                # if self.logs_items['toplevel'].checkState(0) != Qt.CheckState.Checked:
                #     return False

        return True

    def filter_logs(self) -> None:
        block = self.ui.logs_textedit.document().begin()
        while block != self.ui.logs_textedit.document().end():
            userdata = block.userData()
            if userdata is None:
                continue

            block.setVisible(self.entry_visible(userdata.data))

            block = block.next()

        self.ui.logs_textedit.update()

        self.ui.logs_textedit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.logs_textedit.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.reset_scrollbars()

    @Slot(bool)
    def on_acknowledge_button_clicked(self, checked: bool) -> None:
        self.ui.errors_spinbox.setValue(0)
        self.ui.warnings_spinbox.setValue(0)

        self.logged.emit(self.ui.warnings_spinbox.value(),
                         self.ui.errors_spinbox.value())

    def reset_scrollbars(self) -> None:
        horizontal_scrollbar = self.ui.logs_textedit.horizontalScrollBar()
        horizontal_scrollbar.setValue(0)

        vertical_scrollbar = self.ui.logs_textedit.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.reset_scrollbars()

        super().resizeEvent(event)
