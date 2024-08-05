# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'calibration_poses.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QGridLayout, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QScrollArea,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)

from kalao.guis.utils.widgets import (KLabel, KNaNDoubleSpinbox)

class Ui_CalibrationPosesWindow(object):
    def setupUi(self, CalibrationPosesWindow):
        if not CalibrationPosesWindow.objectName():
            CalibrationPosesWindow.setObjectName(u"CalibrationPosesWindow")
        CalibrationPosesWindow.resize(856, 629)
        self.centralwidget = QWidget(CalibrationPosesWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.done_label = KLabel(self.centralwidget)
        self.done_label.setObjectName(u"done_label")
        font = QFont()
        font.setBold(True)
        self.done_label.setFont(font)
        self.done_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.done_label)

        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 836, 448))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.calibration_layout = QGridLayout()
        self.calibration_layout.setObjectName(u"calibration_layout")
        self.exposure_timetime_label = QLabel(self.scrollAreaWidgetContents)
        self.exposure_timetime_label.setObjectName(u"exposure_timetime_label")
        self.exposure_timetime_label.setFont(font)
        self.exposure_timetime_label.setAlignment(Qt.AlignCenter)

        self.calibration_layout.addWidget(self.exposure_timetime_label, 0, 2, 1, 1)

        self.status_label = QLabel(self.scrollAreaWidgetContents)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignCenter)

        self.calibration_layout.addWidget(self.status_label, 0, 4, 1, 1)

        self.filter_label = QLabel(self.scrollAreaWidgetContents)
        self.filter_label.setObjectName(u"filter_label")
        self.filter_label.setFont(font)
        self.filter_label.setAlignment(Qt.AlignCenter)

        self.calibration_layout.addWidget(self.filter_label, 0, 1, 1, 1)

        self.median_label = QLabel(self.scrollAreaWidgetContents)
        self.median_label.setObjectName(u"median_label")
        self.median_label.setFont(font)
        self.median_label.setAlignment(Qt.AlignCenter)

        self.calibration_layout.addWidget(self.median_label, 0, 3, 1, 1)

        self.type_label = QLabel(self.scrollAreaWidgetContents)
        self.type_label.setObjectName(u"type_label")
        self.type_label.setFont(font)
        self.type_label.setAlignment(Qt.AlignCenter)

        self.calibration_layout.addWidget(self.type_label, 0, 0, 1, 1)

        self.calibration_layout.setColumnStretch(0, 1)
        self.calibration_layout.setColumnStretch(1, 1)
        self.calibration_layout.setColumnStretch(2, 1)
        self.calibration_layout.setColumnStretch(3, 1)

        self.verticalLayout_2.addLayout(self.calibration_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.tungsten_status_label = QLabel(self.centralwidget)
        self.tungsten_status_label.setObjectName(u"tungsten_status_label")
        self.tungsten_status_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.tungsten_status_label, 2, 2, 1, 1)

        self.camera_exposure_time_spinbox = KNaNDoubleSpinbox(self.centralwidget)
        self.camera_exposure_time_spinbox.setObjectName(u"camera_exposure_time_spinbox")
        self.camera_exposure_time_spinbox.setReadOnly(True)
        self.camera_exposure_time_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.camera_exposure_time_spinbox.setDecimals(3)
        self.camera_exposure_time_spinbox.setMinimum(-1.000000000000000)
        self.camera_exposure_time_spinbox.setMaximum(999999.000000000000000)

        self.gridLayout.addWidget(self.camera_exposure_time_spinbox, 1, 3, 1, 1)

        self.camera_status_label = QLabel(self.centralwidget)
        self.camera_status_label.setObjectName(u"camera_status_label")
        self.camera_status_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.camera_status_label, 1, 0, 1, 1)

        self.camera_remaining_time_spinbox = KNaNDoubleSpinbox(self.centralwidget)
        self.camera_remaining_time_spinbox.setObjectName(u"camera_remaining_time_spinbox")
        self.camera_remaining_time_spinbox.setReadOnly(True)
        self.camera_remaining_time_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.camera_remaining_time_spinbox.setDecimals(3)
        self.camera_remaining_time_spinbox.setMinimum(-1.000000000000000)
        self.camera_remaining_time_spinbox.setMaximum(999999.000000000000000)

        self.gridLayout.addWidget(self.camera_remaining_time_spinbox, 1, 5, 1, 1)

        self.filterwheel_filter_lineedit = QLineEdit(self.centralwidget)
        self.filterwheel_filter_lineedit.setObjectName(u"filterwheel_filter_lineedit")
        self.filterwheel_filter_lineedit.setReadOnly(True)

        self.gridLayout.addWidget(self.filterwheel_filter_lineedit, 2, 1, 1, 1)

        self.camera_exposure_time_label = QLabel(self.centralwidget)
        self.camera_exposure_time_label.setObjectName(u"camera_exposure_time_label")
        self.camera_exposure_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.camera_exposure_time_label, 1, 2, 1, 1)

        self.camera_status_lineedit = QLineEdit(self.centralwidget)
        self.camera_status_lineedit.setObjectName(u"camera_status_lineedit")
        self.camera_status_lineedit.setReadOnly(True)

        self.gridLayout.addWidget(self.camera_status_lineedit, 1, 1, 1, 1)

        self.tungsten_status_lineedit = QLineEdit(self.centralwidget)
        self.tungsten_status_lineedit.setObjectName(u"tungsten_status_lineedit")
        self.tungsten_status_lineedit.setReadOnly(True)

        self.gridLayout.addWidget(self.tungsten_status_lineedit, 2, 3, 1, 1)

        self.camera_remaining_time_label = QLabel(self.centralwidget)
        self.camera_remaining_time_label.setObjectName(u"camera_remaining_time_label")
        self.camera_remaining_time_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.camera_remaining_time_label, 1, 4, 1, 1)

        self.filterwheel_filter_label = QLabel(self.centralwidget)
        self.filterwheel_filter_label.setObjectName(u"filterwheel_filter_label")
        self.filterwheel_filter_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.filterwheel_filter_label, 2, 0, 1, 1)

        self.flats_label = KLabel(self.centralwidget)
        self.flats_label.setObjectName(u"flats_label")
        self.flats_label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.flats_label, 0, 0, 1, 6)

        self.shutter_label = QLabel(self.centralwidget)
        self.shutter_label.setObjectName(u"shutter_label")
        self.shutter_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.shutter_label, 2, 4, 1, 1)

        self.shutter_status_lineedit = QLineEdit(self.centralwidget)
        self.shutter_status_lineedit.setObjectName(u"shutter_status_lineedit")
        self.shutter_status_lineedit.setReadOnly(True)

        self.gridLayout.addWidget(self.shutter_status_lineedit, 2, 5, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setColumnStretch(3, 1)
        self.gridLayout.setColumnStretch(4, 1)
        self.gridLayout.setColumnStretch(5, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        CalibrationPosesWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(CalibrationPosesWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 856, 23))
        CalibrationPosesWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(CalibrationPosesWindow)
        self.statusbar.setObjectName(u"statusbar")
        CalibrationPosesWindow.setStatusBar(self.statusbar)

        self.retranslateUi(CalibrationPosesWindow)

        QMetaObject.connectSlotsByName(CalibrationPosesWindow)
    # setupUi

    def retranslateUi(self, CalibrationPosesWindow):
        CalibrationPosesWindow.setWindowTitle(QCoreApplication.translate("CalibrationPosesWindow", u"Calibration Poses - KalAO", None))
        self.done_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Calibrations: {current_calib}/{total_calib}", None))
        self.exposure_timetime_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Exposure time", None))
        self.status_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Status", None))
        self.filter_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Filter", None))
        self.median_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Flux", None))
        self.type_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Type", None))
        self.tungsten_status_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Lamp", None))
        self.camera_exposure_time_spinbox.setSuffix(QCoreApplication.translate("CalibrationPosesWindow", u" s", None))
        self.camera_status_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Camera status", None))
        self.camera_remaining_time_spinbox.setSuffix(QCoreApplication.translate("CalibrationPosesWindow", u" s", None))
        self.camera_exposure_time_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Exposure time", None))
        self.camera_remaining_time_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Remaining time", None))
        self.filterwheel_filter_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Filter", None))
        self.flats_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Flats configuration: target flux = {target} ADU, min. exposure time = {min_exposure_time} s, max. exposure time = {max_exposure_time} s", None))
        self.shutter_label.setText(QCoreApplication.translate("CalibrationPosesWindow", u"Shutter", None))
    # retranslateUi

