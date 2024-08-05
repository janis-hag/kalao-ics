# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KNaNDoubleSpinbox, KStatusIndicator)
from . import rc_assets

class Ui_MainWidget(object):
    def setupUi(self, MainWidget):
        if not MainWidget.objectName():
            MainWidget.setObjectName(u"MainWidget")
        MainWidget.resize(1297, 936)
        self.gridLayout = QGridLayout(MainWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.dm_frame = QFrame(MainWidget)
        self.dm_frame.setObjectName(u"dm_frame")
        self.dm_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.dm_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.dm_frame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.dm_frame, 2, 0, 1, 1)

        self.wfs_frame = QFrame(MainWidget)
        self.wfs_frame.setObjectName(u"wfs_frame")
        self.wfs_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.wfs_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.wfs_frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.wfs_frame, 0, 0, 1, 1)

        self.ttm_frame = QFrame(MainWidget)
        self.ttm_frame.setObjectName(u"ttm_frame")
        self.ttm_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.ttm_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_6 = QGridLayout(self.ttm_frame)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.ttm_frame, 2, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.label = QLabel(MainWidget)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(0, 90))
        self.label.setStyleSheet(u"image: url(:/assets/logo/KalAO_logo.svg);\n"
"margin: 10px;")

        self.side_layout.addWidget(self.label)

        self.instrument_groupbox = QGroupBox(MainWidget)
        self.instrument_groupbox.setObjectName(u"instrument_groupbox")
        self.formLayout_4 = QFormLayout(self.instrument_groupbox)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.sequencer_label = QLabel(self.instrument_groupbox)
        self.sequencer_label.setObjectName(u"sequencer_label")
        self.sequencer_label.setMinimumSize(QSize(120, 0))
        self.sequencer_label.setMaximumSize(QSize(120, 16777215))
        self.sequencer_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.sequencer_label)

        self.sequencer_lineedit = QLineEdit(self.instrument_groupbox)
        self.sequencer_lineedit.setObjectName(u"sequencer_lineedit")
        self.sequencer_lineedit.setReadOnly(True)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.sequencer_lineedit)


        self.side_layout.addWidget(self.instrument_groupbox)

        self.ao_groupbox = QGroupBox(MainWidget)
        self.ao_groupbox.setObjectName(u"ao_groupbox")
        self.formLayout_3 = QFormLayout(self.ao_groupbox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.dmloop_label = QLabel(self.ao_groupbox)
        self.dmloop_label.setObjectName(u"dmloop_label")
        self.dmloop_label.setMinimumSize(QSize(120, 0))
        self.dmloop_label.setMaximumSize(QSize(120, 16777215))
        self.dmloop_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.dmloop_label)

        self.dmloop_indicator = KStatusIndicator(self.ao_groupbox)
        self.dmloop_indicator.setObjectName(u"dmloop_indicator")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dmloop_indicator.sizePolicy().hasHeightForWidth())
        self.dmloop_indicator.setSizePolicy(sizePolicy)
        self.dmloop_indicator.setMinimumSize(QSize(30, 30))
        self.dmloop_indicator.setMaximumSize(QSize(30, 30))

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.dmloop_indicator)

        self.ttmloop_label = QLabel(self.ao_groupbox)
        self.ttmloop_label.setObjectName(u"ttmloop_label")
        self.ttmloop_label.setMinimumSize(QSize(120, 0))
        self.ttmloop_label.setMaximumSize(QSize(120, 16777215))
        self.ttmloop_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.ttmloop_label)

        self.ttmloop_indicator = KStatusIndicator(self.ao_groupbox)
        self.ttmloop_indicator.setObjectName(u"ttmloop_indicator")
        sizePolicy.setHeightForWidth(self.ttmloop_indicator.sizePolicy().hasHeightForWidth())
        self.ttmloop_indicator.setSizePolicy(sizePolicy)
        self.ttmloop_indicator.setMinimumSize(QSize(30, 30))
        self.ttmloop_indicator.setMaximumSize(QSize(30, 30))

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.ttmloop_indicator)


        self.side_layout.addWidget(self.ao_groupbox)

        self.camera_groupbox = QGroupBox(MainWidget)
        self.camera_groupbox.setObjectName(u"camera_groupbox")
        self.formLayout_2 = QFormLayout(self.camera_groupbox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.camera_status_label = QLabel(self.camera_groupbox)
        self.camera_status_label.setObjectName(u"camera_status_label")
        self.camera_status_label.setMinimumSize(QSize(120, 0))
        self.camera_status_label.setMaximumSize(QSize(120, 16777215))
        self.camera_status_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.camera_status_label)

        self.cameras_status_indicator = KStatusIndicator(self.camera_groupbox)
        self.cameras_status_indicator.setObjectName(u"cameras_status_indicator")
        sizePolicy.setHeightForWidth(self.cameras_status_indicator.sizePolicy().hasHeightForWidth())
        self.cameras_status_indicator.setSizePolicy(sizePolicy)
        self.cameras_status_indicator.setMinimumSize(QSize(30, 30))
        self.cameras_status_indicator.setMaximumSize(QSize(30, 30))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.cameras_status_indicator)

        self.camera_exposure_time_label = QLabel(self.camera_groupbox)
        self.camera_exposure_time_label.setObjectName(u"camera_exposure_time_label")
        self.camera_exposure_time_label.setMinimumSize(QSize(120, 0))
        self.camera_exposure_time_label.setMaximumSize(QSize(120, 16777215))
        self.camera_exposure_time_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.camera_exposure_time_label)

        self.camera_exposure_time_spinbox = KNaNDoubleSpinbox(self.camera_groupbox)
        self.camera_exposure_time_spinbox.setObjectName(u"camera_exposure_time_spinbox")
        self.camera_exposure_time_spinbox.setReadOnly(True)
        self.camera_exposure_time_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.camera_exposure_time_spinbox.setKeyboardTracking(False)
        self.camera_exposure_time_spinbox.setDecimals(3)
        self.camera_exposure_time_spinbox.setMinimum(0.001000000000000)
        self.camera_exposure_time_spinbox.setMaximum(99999999.000000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.camera_exposure_time_spinbox)

        self.camera_remaining_time_label = QLabel(self.camera_groupbox)
        self.camera_remaining_time_label.setObjectName(u"camera_remaining_time_label")
        self.camera_remaining_time_label.setMinimumSize(QSize(120, 0))
        self.camera_remaining_time_label.setMaximumSize(QSize(120, 16777215))
        self.camera_remaining_time_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.camera_remaining_time_label)

        self.camera_remaining_time_spinbox = KNaNDoubleSpinbox(self.camera_groupbox)
        self.camera_remaining_time_spinbox.setObjectName(u"camera_remaining_time_spinbox")
        self.camera_remaining_time_spinbox.setReadOnly(True)
        self.camera_remaining_time_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.camera_remaining_time_spinbox.setKeyboardTracking(False)
        self.camera_remaining_time_spinbox.setDecimals(3)
        self.camera_remaining_time_spinbox.setMinimum(0.000000000000000)
        self.camera_remaining_time_spinbox.setMaximum(99999999.000000000000000)

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.camera_remaining_time_spinbox)

        self.camera_remaining_frames_label = QLabel(self.camera_groupbox)
        self.camera_remaining_frames_label.setObjectName(u"camera_remaining_frames_label")
        self.camera_remaining_frames_label.setMinimumSize(QSize(120, 0))
        self.camera_remaining_frames_label.setMaximumSize(QSize(120, 16777215))
        self.camera_remaining_frames_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.camera_remaining_frames_label)

        self.camera_remaining_frames_spinbox = QSpinBox(self.camera_groupbox)
        self.camera_remaining_frames_spinbox.setObjectName(u"camera_remaining_frames_spinbox")
        self.camera_remaining_frames_spinbox.setReadOnly(True)
        self.camera_remaining_frames_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.camera_remaining_frames_spinbox.setKeyboardTracking(False)
        self.camera_remaining_frames_spinbox.setMinimum(-1)
        self.camera_remaining_frames_spinbox.setMaximum(9999)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.camera_remaining_frames_spinbox)

        self.camera_ccd_temperature_label = QLabel(self.camera_groupbox)
        self.camera_ccd_temperature_label.setObjectName(u"camera_ccd_temperature_label")
        self.camera_ccd_temperature_label.setMinimumSize(QSize(120, 0))
        self.camera_ccd_temperature_label.setMaximumSize(QSize(120, 16777215))
        self.camera_ccd_temperature_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.camera_ccd_temperature_label)

        self.camera_ccd_temperature_spinbox = KNaNDoubleSpinbox(self.camera_groupbox)
        self.camera_ccd_temperature_spinbox.setObjectName(u"camera_ccd_temperature_spinbox")
        self.camera_ccd_temperature_spinbox.setReadOnly(True)
        self.camera_ccd_temperature_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.camera_ccd_temperature_spinbox.setKeyboardTracking(False)
        self.camera_ccd_temperature_spinbox.setDecimals(1)
        self.camera_ccd_temperature_spinbox.setMinimum(-100.000000000000000)
        self.camera_ccd_temperature_spinbox.setMaximum(100.000000000000000)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.camera_ccd_temperature_spinbox)


        self.side_layout.addWidget(self.camera_groupbox)

        self.wfs_groupbox = QGroupBox(MainWidget)
        self.wfs_groupbox.setObjectName(u"wfs_groupbox")
        self.formLayout = QFormLayout(self.wfs_groupbox)
        self.formLayout.setObjectName(u"formLayout")
        self.wfs_acquisition_label = QLabel(self.wfs_groupbox)
        self.wfs_acquisition_label.setObjectName(u"wfs_acquisition_label")
        self.wfs_acquisition_label.setMinimumSize(QSize(120, 0))
        self.wfs_acquisition_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_acquisition_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.wfs_acquisition_label)

        self.wfs_acquisition_indicator = KStatusIndicator(self.wfs_groupbox)
        self.wfs_acquisition_indicator.setObjectName(u"wfs_acquisition_indicator")
        sizePolicy.setHeightForWidth(self.wfs_acquisition_indicator.sizePolicy().hasHeightForWidth())
        self.wfs_acquisition_indicator.setSizePolicy(sizePolicy)
        self.wfs_acquisition_indicator.setMinimumSize(QSize(30, 30))
        self.wfs_acquisition_indicator.setMaximumSize(QSize(30, 30))

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.wfs_acquisition_indicator)

        self.wfs_autogain_label = QLabel(self.wfs_groupbox)
        self.wfs_autogain_label.setObjectName(u"wfs_autogain_label")
        self.wfs_autogain_label.setMinimumSize(QSize(120, 0))
        self.wfs_autogain_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_autogain_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.wfs_autogain_label)

        self.wfs_autogain_indicator = KStatusIndicator(self.wfs_groupbox)
        self.wfs_autogain_indicator.setObjectName(u"wfs_autogain_indicator")
        sizePolicy.setHeightForWidth(self.wfs_autogain_indicator.sizePolicy().hasHeightForWidth())
        self.wfs_autogain_indicator.setSizePolicy(sizePolicy)
        self.wfs_autogain_indicator.setMinimumSize(QSize(30, 30))
        self.wfs_autogain_indicator.setMaximumSize(QSize(30, 30))

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.wfs_autogain_indicator)

        self.wfs_emgain_label = QLabel(self.wfs_groupbox)
        self.wfs_emgain_label.setObjectName(u"wfs_emgain_label")
        self.wfs_emgain_label.setMinimumSize(QSize(120, 0))
        self.wfs_emgain_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_emgain_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.wfs_emgain_label)

        self.wfs_emgain_spinbox = QSpinBox(self.wfs_groupbox)
        self.wfs_emgain_spinbox.setObjectName(u"wfs_emgain_spinbox")
        self.wfs_emgain_spinbox.setReadOnly(True)
        self.wfs_emgain_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.wfs_emgain_spinbox.setKeyboardTracking(False)
        self.wfs_emgain_spinbox.setMinimum(-1)
        self.wfs_emgain_spinbox.setMaximum(9999)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.wfs_emgain_spinbox)

        self.wfs_exposuretime_label = QLabel(self.wfs_groupbox)
        self.wfs_exposuretime_label.setObjectName(u"wfs_exposuretime_label")
        self.wfs_exposuretime_label.setMinimumSize(QSize(120, 0))
        self.wfs_exposuretime_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_exposuretime_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.wfs_exposuretime_label)

        self.wfs_exposuretime_spinbox = KNaNDoubleSpinbox(self.wfs_groupbox)
        self.wfs_exposuretime_spinbox.setObjectName(u"wfs_exposuretime_spinbox")
        self.wfs_exposuretime_spinbox.setReadOnly(True)
        self.wfs_exposuretime_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.wfs_exposuretime_spinbox.setKeyboardTracking(False)
        self.wfs_exposuretime_spinbox.setDecimals(2)
        self.wfs_exposuretime_spinbox.setMinimum(0.000000000000000)
        self.wfs_exposuretime_spinbox.setMaximum(99999999.000000000000000)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.wfs_exposuretime_spinbox)

        self.wfs_framerate_label = QLabel(self.wfs_groupbox)
        self.wfs_framerate_label.setObjectName(u"wfs_framerate_label")
        self.wfs_framerate_label.setMinimumSize(QSize(120, 0))
        self.wfs_framerate_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_framerate_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.wfs_framerate_label)

        self.wfs_framerate_spinbox = KNaNDoubleSpinbox(self.wfs_groupbox)
        self.wfs_framerate_spinbox.setObjectName(u"wfs_framerate_spinbox")
        self.wfs_framerate_spinbox.setReadOnly(True)
        self.wfs_framerate_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.wfs_framerate_spinbox.setKeyboardTracking(False)
        self.wfs_framerate_spinbox.setDecimals(2)
        self.wfs_framerate_spinbox.setMinimum(0.000000000000000)
        self.wfs_framerate_spinbox.setMaximum(10000.000000000000000)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.wfs_framerate_spinbox)

        self.wfs_ccd_temperature_label = QLabel(self.wfs_groupbox)
        self.wfs_ccd_temperature_label.setObjectName(u"wfs_ccd_temperature_label")
        self.wfs_ccd_temperature_label.setMinimumSize(QSize(120, 0))
        self.wfs_ccd_temperature_label.setMaximumSize(QSize(120, 16777215))
        self.wfs_ccd_temperature_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.wfs_ccd_temperature_label)

        self.wfs_ccd_temperature_spinbox = KNaNDoubleSpinbox(self.wfs_groupbox)
        self.wfs_ccd_temperature_spinbox.setObjectName(u"wfs_ccd_temperature_spinbox")
        self.wfs_ccd_temperature_spinbox.setReadOnly(True)
        self.wfs_ccd_temperature_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.wfs_ccd_temperature_spinbox.setKeyboardTracking(False)
        self.wfs_ccd_temperature_spinbox.setDecimals(1)
        self.wfs_ccd_temperature_spinbox.setMinimum(-100.000000000000000)
        self.wfs_ccd_temperature_spinbox.setMaximum(100.000000000000000)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.wfs_ccd_temperature_spinbox)


        self.side_layout.addWidget(self.wfs_groupbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.options_groupbox = QGroupBox(MainWidget)
        self.options_groupbox.setObjectName(u"options_groupbox")
        self.verticalLayout_7 = QVBoxLayout(self.options_groupbox)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.onsky_checkbox = QCheckBox(self.options_groupbox)
        self.onsky_checkbox.setObjectName(u"onsky_checkbox")

        self.verticalLayout_7.addWidget(self.onsky_checkbox)

        self.masks_checkbox = QCheckBox(self.options_groupbox)
        self.masks_checkbox.setObjectName(u"masks_checkbox")
        self.masks_checkbox.setChecked(True)

        self.verticalLayout_7.addWidget(self.masks_checkbox)

        self.colormap_checkbox = QCheckBox(self.options_groupbox)
        self.colormap_checkbox.setObjectName(u"colormap_checkbox")

        self.verticalLayout_7.addWidget(self.colormap_checkbox)


        self.side_layout.addWidget(self.options_groupbox)


        self.gridLayout.addLayout(self.side_layout, 0, 2, 3, 1)

        self.camera_frame = QFrame(MainWidget)
        self.camera_frame.setObjectName(u"camera_frame")
        self.camera_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.camera_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_7 = QGridLayout(self.camera_frame)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.camera_frame, 0, 1, 1, 1)

        self.flux_frame = QFrame(MainWidget)
        self.flux_frame.setObjectName(u"flux_frame")
        self.flux_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.flux_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_5 = QGridLayout(self.flux_frame)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.flux_frame, 1, 0, 1, 1)

        self.slopes_frame = QFrame(MainWidget)
        self.slopes_frame.setObjectName(u"slopes_frame")
        self.slopes_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.slopes_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_4 = QGridLayout(self.slopes_frame)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.slopes_frame, 1, 1, 1, 1)

        self.gridLayout.setRowStretch(0, 2)
        self.gridLayout.setRowStretch(1, 1)
        self.gridLayout.setRowStretch(2, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(MainWidget)

        QMetaObject.connectSlotsByName(MainWidget)
    # setupUi

    def retranslateUi(self, MainWidget):
        MainWidget.setWindowTitle(QCoreApplication.translate("MainWidget", u"Main - KalAO", None))
        self.instrument_groupbox.setTitle(QCoreApplication.translate("MainWidget", u"Instrument", None))
        self.sequencer_label.setText(QCoreApplication.translate("MainWidget", u"Sequencer", None))
        self.ao_groupbox.setTitle(QCoreApplication.translate("MainWidget", u"Adaptive Optics", None))
        self.dmloop_label.setText(QCoreApplication.translate("MainWidget", u"DM Loop", None))
        self.ttmloop_label.setText(QCoreApplication.translate("MainWidget", u"TTM Loop", None))
        self.camera_groupbox.setTitle(QCoreApplication.translate("MainWidget", u"Science Camera", None))
        self.camera_status_label.setText(QCoreApplication.translate("MainWidget", u"Status", None))
        self.camera_exposure_time_label.setText(QCoreApplication.translate("MainWidget", u"Exposure time", None))
        self.camera_exposure_time_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" s", None))
        self.camera_remaining_time_label.setText(QCoreApplication.translate("MainWidget", u"Time remaining", None))
        self.camera_remaining_time_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" s", None))
        self.camera_remaining_frames_label.setText(QCoreApplication.translate("MainWidget", u"Frames remaining", None))
        self.camera_remaining_frames_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" frames", None))
        self.camera_ccd_temperature_label.setText(QCoreApplication.translate("MainWidget", u"CCD Temperature", None))
        self.camera_ccd_temperature_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" \u00b0C", None))
        self.wfs_groupbox.setTitle(QCoreApplication.translate("MainWidget", u"Wavefront Sensor", None))
        self.wfs_acquisition_label.setText(QCoreApplication.translate("MainWidget", u"Acquisition", None))
        self.wfs_autogain_label.setText(QCoreApplication.translate("MainWidget", u"Autogain", None))
        self.wfs_emgain_label.setText(QCoreApplication.translate("MainWidget", u"EM Gain", None))
        self.wfs_emgain_spinbox.setSuffix("")
        self.wfs_exposuretime_label.setText(QCoreApplication.translate("MainWidget", u"Exposure time", None))
        self.wfs_exposuretime_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" ms", None))
        self.wfs_framerate_label.setText(QCoreApplication.translate("MainWidget", u"Frame rate", None))
        self.wfs_framerate_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" Hz", None))
        self.wfs_ccd_temperature_label.setText(QCoreApplication.translate("MainWidget", u"CCD Temperature", None))
        self.wfs_ccd_temperature_spinbox.setSuffix(QCoreApplication.translate("MainWidget", u" \u00b0C", None))
        self.options_groupbox.setTitle(QCoreApplication.translate("MainWidget", u"Options", None))
        self.onsky_checkbox.setText(QCoreApplication.translate("MainWidget", u"Use On-Sky Units", None))
        self.masks_checkbox.setText(QCoreApplication.translate("MainWidget", u"Use Masks", None))
        self.colormap_checkbox.setText(QCoreApplication.translate("MainWidget", u"Grayscale Colormap (w/ saturation)", None))
    # retranslateUi

