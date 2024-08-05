# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'logs.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDateTimeEdit, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTreeWidget, QTreeWidgetItem, QWidget)

from kalao.guis.utils.widgets import KDateTimeEdit
from . import rc_assets

class Ui_LogsWidget(object):
    def setupUi(self, LogsWidget):
        if not LogsWidget.objectName():
            LogsWidget.setObjectName(u"LogsWidget")
        LogsWidget.resize(1073, 593)
        self.gridLayout = QGridLayout(LogsWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.clear_services_button = QPushButton(LogsWidget)
        self.clear_services_button.setObjectName(u"clear_services_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/edit-clear-all.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.clear_services_button.setIcon(icon)

        self.gridLayout.addWidget(self.clear_services_button, 3, 1, 1, 1)

        self.clear_levels_button = QPushButton(LogsWidget)
        self.clear_levels_button.setObjectName(u"clear_levels_button")
        self.clear_levels_button.setIcon(icon)

        self.gridLayout.addWidget(self.clear_levels_button, 2, 1, 1, 1)

        self.check_all_button = QPushButton(LogsWidget)
        self.check_all_button.setObjectName(u"check_all_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/checkmark.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.check_all_button.setIcon(icon1)

        self.gridLayout.addWidget(self.check_all_button, 5, 1, 1, 1)

        self.clear_logs_button = QPushButton(LogsWidget)
        self.clear_logs_button.setObjectName(u"clear_logs_button")
        self.clear_logs_button.setIcon(icon)

        self.gridLayout.addWidget(self.clear_logs_button, 4, 1, 1, 1)

        self.total_layout = QHBoxLayout()
        self.total_layout.setObjectName(u"total_layout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.total_layout.addItem(self.horizontalSpacer)

        self.warnings_label = QLabel(LogsWidget)
        self.warnings_label.setObjectName(u"warnings_label")

        self.total_layout.addWidget(self.warnings_label)

        self.warnings_spinbox = QSpinBox(LogsWidget)
        self.warnings_spinbox.setObjectName(u"warnings_spinbox")
        self.warnings_spinbox.setReadOnly(True)
        self.warnings_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.warnings_spinbox.setMaximum(9999)

        self.total_layout.addWidget(self.warnings_spinbox)

        self.horizontalSpacer_2 = QSpacerItem(30, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.total_layout.addItem(self.horizontalSpacer_2)

        self.errors_label = QLabel(LogsWidget)
        self.errors_label.setObjectName(u"errors_label")

        self.total_layout.addWidget(self.errors_label)

        self.errors_spinbox = QSpinBox(LogsWidget)
        self.errors_spinbox.setObjectName(u"errors_spinbox")
        self.errors_spinbox.setReadOnly(True)
        self.errors_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.errors_spinbox.setMaximum(9999)

        self.total_layout.addWidget(self.errors_spinbox)

        self.horizontalSpacer_3 = QSpacerItem(30, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.total_layout.addItem(self.horizontalSpacer_3)

        self.acknowledge_button = QPushButton(LogsWidget)
        self.acknowledge_button.setObjectName(u"acknowledge_button")
        self.acknowledge_button.setIcon(icon1)

        self.total_layout.addWidget(self.acknowledge_button)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.total_layout.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.total_layout, 5, 0, 1, 1)

        self.logs_textedit = QPlainTextEdit(LogsWidget)
        self.logs_textedit.setObjectName(u"logs_textedit")
        palette = QPalette()
        brush = QBrush(QColor(252, 252, 252, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Text, brush)
        brush1 = QBrush(QColor(35, 38, 39, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Base, brush1)
        brush2 = QBrush(QColor(176, 176, 176, 255))
        brush2.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush2)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush2)
#endif
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush2)
#endif
        self.logs_textedit.setPalette(palette)
        font = QFont()
        font.setFamilies([u"Roboto Mono"])
        self.logs_textedit.setFont(font)
        self.logs_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.logs_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.logs_textedit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.logs_textedit.setCursorWidth(0)

        self.gridLayout.addWidget(self.logs_textedit, 1, 0, 4, 1)

        self.time_layout = QHBoxLayout()
        self.time_layout.setObjectName(u"time_layout")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.time_layout.addItem(self.horizontalSpacer_5)

        self.since_label = QLabel(LogsWidget)
        self.since_label.setObjectName(u"since_label")

        self.time_layout.addWidget(self.since_label)

        self.since_datetimeedit = KDateTimeEdit(LogsWidget)
        self.since_datetimeedit.setObjectName(u"since_datetimeedit")
        self.since_datetimeedit.setCurrentSection(QDateTimeEdit.Section.HourSection)

        self.time_layout.addWidget(self.since_datetimeedit)

        self.horizontalSpacer_6 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.time_layout.addItem(self.horizontalSpacer_6)

        self.until_label = QLabel(LogsWidget)
        self.until_label.setObjectName(u"until_label")

        self.time_layout.addWidget(self.until_label)

        self.until_datetimeedit = KDateTimeEdit(LogsWidget)
        self.until_datetimeedit.setObjectName(u"until_datetimeedit")
        self.until_datetimeedit.setCurrentSection(QDateTimeEdit.Section.HourSection)

        self.time_layout.addWidget(self.until_datetimeedit)

        self.horizontalSpacer_8 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.time_layout.addItem(self.horizontalSpacer_8)

        self.retieve_button = QPushButton(LogsWidget)
        self.retieve_button.setObjectName(u"retieve_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/download.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.retieve_button.setIcon(icon2)

        self.time_layout.addWidget(self.retieve_button)

        self.live_button = QPushButton(LogsWidget)
        self.live_button.setObjectName(u"live_button")
        icon3 = QIcon()
        icon3.addFile(u":/assets/icons/media-record.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.live_button.setIcon(icon3)

        self.time_layout.addWidget(self.live_button)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.time_layout.addItem(self.horizontalSpacer_7)


        self.gridLayout.addLayout(self.time_layout, 0, 0, 1, 1)

        self.filters_tree = QTreeWidget(LogsWidget)
        self.filters_tree.setObjectName(u"filters_tree")
        self.filters_tree.setMaximumSize(QSize(200, 16777215))
        self.filters_tree.setProperty("showDropIndicator", False)
        self.filters_tree.setRootIsDecorated(False)

        self.gridLayout.addWidget(self.filters_tree, 0, 1, 2, 1)

        self.gridLayout.setRowStretch(1, 1)
        self.gridLayout.setColumnStretch(0, 1)

        self.retranslateUi(LogsWidget)

        QMetaObject.connectSlotsByName(LogsWidget)
    # setupUi

    def retranslateUi(self, LogsWidget):
        LogsWidget.setWindowTitle(QCoreApplication.translate("LogsWidget", u"Logs - KalAO", None))
        self.clear_services_button.setText(QCoreApplication.translate("LogsWidget", u"Clear Services", None))
        self.clear_levels_button.setText(QCoreApplication.translate("LogsWidget", u"Clear Levels", None))
        self.check_all_button.setText(QCoreApplication.translate("LogsWidget", u"Check All", None))
        self.clear_logs_button.setText(QCoreApplication.translate("LogsWidget", u"Clear Logs", None))
        self.warnings_label.setText(QCoreApplication.translate("LogsWidget", u"Warnings", None))
        self.errors_label.setText(QCoreApplication.translate("LogsWidget", u"Errors", None))
        self.acknowledge_button.setText(QCoreApplication.translate("LogsWidget", u"Acknowledge warnings and errors", None))
        self.logs_textedit.setPlaceholderText(QCoreApplication.translate("LogsWidget", u"Logs will appear here ...", None))
        self.since_label.setText(QCoreApplication.translate("LogsWidget", u"Since", None))
        self.since_datetimeedit.setDisplayFormat(QCoreApplication.translate("LogsWidget", u"HH:mm:ss dd.MM.yy", None))
        self.until_label.setText(QCoreApplication.translate("LogsWidget", u"Until", None))
        self.until_datetimeedit.setDisplayFormat(QCoreApplication.translate("LogsWidget", u"HH:mm:ss dd.MM.yy", None))
        self.retieve_button.setText(QCoreApplication.translate("LogsWidget", u"Retrieve", None))
        self.live_button.setText(QCoreApplication.translate("LogsWidget", u"Live", None))
        ___qtreewidgetitem = self.filters_tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("LogsWidget", u"Filters", None));
    # retranslateUi

