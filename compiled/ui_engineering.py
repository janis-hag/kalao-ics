# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'engineering.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KLabel, KNaNDoubleSpinbox, KStatusIndicator)
from . import rc_assets

class Ui_EngineeringWidget(object):
    def setupUi(self, EngineeringWidget):
        if not EngineeringWidget.objectName():
            EngineeringWidget.setObjectName(u"EngineeringWidget")
        EngineeringWidget.resize(1562, 1086)
        self.horizontalLayout_3 = QHBoxLayout(EngineeringWidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.left_pane_layout = QVBoxLayout()
        self.left_pane_layout.setObjectName(u"left_pane_layout")
        self.plc_groupbox = QGroupBox(EngineeringWidget)
        self.plc_groupbox.setObjectName(u"plc_groupbox")
        self.plc_groupbox.setCheckable(False)
        self.gridLayout_4 = QGridLayout(self.plc_groupbox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.adc1_indicator = KStatusIndicator(self.plc_groupbox)
        self.adc1_indicator.setObjectName(u"adc1_indicator")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.adc1_indicator.sizePolicy().hasHeightForWidth())
        self.adc1_indicator.setSizePolicy(sizePolicy)
        self.adc1_indicator.setMinimumSize(QSize(20, 20))
        self.adc1_indicator.setMaximumSize(QSize(20, 20))
        self.adc1_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.adc1_indicator, 6, 1, 1, 1)

        self.adc2_label = QLabel(self.plc_groupbox)
        self.adc2_label.setObjectName(u"adc2_label")
        self.adc2_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.adc2_label, 7, 0, 1, 1)

        self.adc1_spinbox = KNaNDoubleSpinbox(self.plc_groupbox)
        self.adc1_spinbox.setObjectName(u"adc1_spinbox")
        self.adc1_spinbox.setKeyboardTracking(False)
        self.adc1_spinbox.setMinimum(-360.000000000000000)
        self.adc1_spinbox.setMaximum(360.000000000000000)
        self.adc1_spinbox.setSingleStep(0.100000000000000)

        self.gridLayout_4.addWidget(self.adc1_spinbox, 6, 2, 1, 1)

        self.adc1_label = QLabel(self.plc_groupbox)
        self.adc1_label.setObjectName(u"adc1_label")
        self.adc1_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.adc1_label, 6, 0, 1, 1)

        self.laser_layout = QHBoxLayout()
        self.laser_layout.setObjectName(u"laser_layout")
        self.laser_status_checkbox = QCheckBox(self.plc_groupbox)
        self.laser_status_checkbox.setObjectName(u"laser_status_checkbox")

        self.laser_layout.addWidget(self.laser_status_checkbox)

        self.laser_power_spinbox = QDoubleSpinBox(self.plc_groupbox)
        self.laser_power_spinbox.setObjectName(u"laser_power_spinbox")
        self.laser_power_spinbox.setKeyboardTracking(False)
        self.laser_power_spinbox.setMaximum(8.000000000000000)
        self.laser_power_spinbox.setSingleStep(0.100000000000000)

        self.laser_layout.addWidget(self.laser_power_spinbox)

        self.laser_layout.setStretch(1, 1)

        self.gridLayout_4.addLayout(self.laser_layout, 4, 2, 1, 1)

        self.frame = QFrame(self.plc_groupbox)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.HLine)
        self.frame.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_4.addWidget(self.frame, 10, 0, 1, 6)

        self.shutter_label = QLabel(self.plc_groupbox)
        self.shutter_label.setObjectName(u"shutter_label")
        self.shutter_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.shutter_label, 0, 0, 1, 1)

        self.flipmirror_combobox = QComboBox(self.plc_groupbox)
        self.flipmirror_combobox.setObjectName(u"flipmirror_combobox")

        self.gridLayout_4.addWidget(self.flipmirror_combobox, 1, 2, 1, 1)

        self.calibunit_label = QLabel(self.plc_groupbox)
        self.calibunit_label.setObjectName(u"calibunit_label")
        self.calibunit_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.calibunit_label, 2, 0, 1, 1)

        self.shutter_indicator = KStatusIndicator(self.plc_groupbox)
        self.shutter_indicator.setObjectName(u"shutter_indicator")
        sizePolicy.setHeightForWidth(self.shutter_indicator.sizePolicy().hasHeightForWidth())
        self.shutter_indicator.setSizePolicy(sizePolicy)
        self.shutter_indicator.setMinimumSize(QSize(20, 20))
        self.shutter_indicator.setMaximumSize(QSize(20, 20))
        self.shutter_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.shutter_indicator, 0, 1, 1, 1)

        self.tungsten_status_indicator = KStatusIndicator(self.plc_groupbox)
        self.tungsten_status_indicator.setObjectName(u"tungsten_status_indicator")
        sizePolicy.setHeightForWidth(self.tungsten_status_indicator.sizePolicy().hasHeightForWidth())
        self.tungsten_status_indicator.setSizePolicy(sizePolicy)
        self.tungsten_status_indicator.setMinimumSize(QSize(20, 20))
        self.tungsten_status_indicator.setMaximumSize(QSize(20, 20))
        self.tungsten_status_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.tungsten_status_indicator, 3, 1, 1, 1)

        self.calibunit_spinbox = KNaNDoubleSpinbox(self.plc_groupbox)
        self.calibunit_spinbox.setObjectName(u"calibunit_spinbox")
        self.calibunit_spinbox.setKeyboardTracking(False)
        self.calibunit_spinbox.setMaximum(100.000000000000000)
        self.calibunit_spinbox.setSingleStep(0.100000000000000)

        self.gridLayout_4.addWidget(self.calibunit_spinbox, 2, 2, 1, 1)

        self.filterwheel_label = QLabel(self.plc_groupbox)
        self.filterwheel_label.setObjectName(u"filterwheel_label")
        self.filterwheel_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.filterwheel_label, 5, 0, 1, 1)

        self.calibunit_laser_button = QPushButton(self.plc_groupbox)
        self.calibunit_laser_button.setObjectName(u"calibunit_laser_button")

        self.gridLayout_4.addWidget(self.calibunit_laser_button, 2, 4, 1, 1)

        self.flipmirror_label = QLabel(self.plc_groupbox)
        self.flipmirror_label.setObjectName(u"flipmirror_label")
        self.flipmirror_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.flipmirror_label, 1, 0, 1, 1)

        self.init_layout = QGridLayout()
        self.init_layout.setObjectName(u"init_layout")
        self.shutter_init_button = QPushButton(self.plc_groupbox)
        self.shutter_init_button.setObjectName(u"shutter_init_button")

        self.init_layout.addWidget(self.shutter_init_button, 0, 0, 1, 1)

        self.flipmirror_init_button = QPushButton(self.plc_groupbox)
        self.flipmirror_init_button.setObjectName(u"flipmirror_init_button")

        self.init_layout.addWidget(self.flipmirror_init_button, 1, 0, 1, 1)

        self.calibunit_init_button = QPushButton(self.plc_groupbox)
        self.calibunit_init_button.setObjectName(u"calibunit_init_button")

        self.init_layout.addWidget(self.calibunit_init_button, 0, 1, 1, 1)

        self.filterwheel_init_button = QPushButton(self.plc_groupbox)
        self.filterwheel_init_button.setObjectName(u"filterwheel_init_button")

        self.init_layout.addWidget(self.filterwheel_init_button, 1, 1, 1, 1)

        self.tungsten_init_button = QPushButton(self.plc_groupbox)
        self.tungsten_init_button.setObjectName(u"tungsten_init_button")

        self.init_layout.addWidget(self.tungsten_init_button, 0, 2, 1, 1)

        self.laser_init_button = QPushButton(self.plc_groupbox)
        self.laser_init_button.setObjectName(u"laser_init_button")

        self.init_layout.addWidget(self.laser_init_button, 1, 2, 1, 1)

        self.adc1_init_button = QPushButton(self.plc_groupbox)
        self.adc1_init_button.setObjectName(u"adc1_init_button")

        self.init_layout.addWidget(self.adc1_init_button, 0, 3, 1, 1)

        self.adc2_init_button = QPushButton(self.plc_groupbox)
        self.adc2_init_button.setObjectName(u"adc2_init_button")

        self.init_layout.addWidget(self.adc2_init_button, 1, 3, 1, 1)


        self.gridLayout_4.addLayout(self.init_layout, 11, 1, 1, 5)

        self.adc2_stop_button = QPushButton(self.plc_groupbox)
        self.adc2_stop_button.setObjectName(u"adc2_stop_button")

        self.gridLayout_4.addWidget(self.adc2_stop_button, 7, 3, 1, 1)

        self.laser_label = QLabel(self.plc_groupbox)
        self.laser_label.setObjectName(u"laser_label")
        self.laser_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.laser_label, 4, 0, 1, 1)

        self.calibunit_indicator = KStatusIndicator(self.plc_groupbox)
        self.calibunit_indicator.setObjectName(u"calibunit_indicator")
        sizePolicy.setHeightForWidth(self.calibunit_indicator.sizePolicy().hasHeightForWidth())
        self.calibunit_indicator.setSizePolicy(sizePolicy)
        self.calibunit_indicator.setMinimumSize(QSize(20, 20))
        self.calibunit_indicator.setMaximumSize(QSize(20, 20))
        self.calibunit_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibunit_indicator, 2, 1, 1, 1)

        self.adc2_spinbox = KNaNDoubleSpinbox(self.plc_groupbox)
        self.adc2_spinbox.setObjectName(u"adc2_spinbox")
        self.adc2_spinbox.setKeyboardTracking(False)
        self.adc2_spinbox.setMinimum(-360.000000000000000)
        self.adc2_spinbox.setMaximum(360.000000000000000)
        self.adc2_spinbox.setSingleStep(0.100000000000000)

        self.gridLayout_4.addWidget(self.adc2_spinbox, 7, 2, 1, 1)

        self.tungsten_status_checkbox = QCheckBox(self.plc_groupbox)
        self.tungsten_status_checkbox.setObjectName(u"tungsten_status_checkbox")

        self.gridLayout_4.addWidget(self.tungsten_status_checkbox, 3, 2, 1, 1)

        self.tungsten_label = QLabel(self.plc_groupbox)
        self.tungsten_label.setObjectName(u"tungsten_label")
        self.tungsten_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.tungsten_label, 3, 0, 1, 1)

        self.adc1_stop_button = QPushButton(self.plc_groupbox)
        self.adc1_stop_button.setObjectName(u"adc1_stop_button")

        self.gridLayout_4.addWidget(self.adc1_stop_button, 6, 3, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 14, 0, 1, 6)

        self.filterwheel_combobox = QComboBox(self.plc_groupbox)
        self.filterwheel_combobox.setObjectName(u"filterwheel_combobox")

        self.gridLayout_4.addWidget(self.filterwheel_combobox, 5, 2, 1, 1)

        self.calibunit_stop_button = QPushButton(self.plc_groupbox)
        self.calibunit_stop_button.setObjectName(u"calibunit_stop_button")

        self.gridLayout_4.addWidget(self.calibunit_stop_button, 2, 3, 1, 1)

        self.laser_indicator = KStatusIndicator(self.plc_groupbox)
        self.laser_indicator.setObjectName(u"laser_indicator")
        sizePolicy.setHeightForWidth(self.laser_indicator.sizePolicy().hasHeightForWidth())
        self.laser_indicator.setSizePolicy(sizePolicy)
        self.laser_indicator.setMinimumSize(QSize(20, 20))
        self.laser_indicator.setMaximumSize(QSize(20, 20))
        self.laser_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.laser_indicator, 4, 1, 1, 1)

        self.adc_angle_label = QLabel(self.plc_groupbox)
        self.adc_angle_label.setObjectName(u"adc_angle_label")
        self.adc_angle_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.adc_angle_label, 8, 0, 1, 1)

        self.init_label = QLabel(self.plc_groupbox)
        self.init_label.setObjectName(u"init_label")
        self.init_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.init_label, 11, 0, 1, 1)

        self.cooling_layout = QHBoxLayout()
        self.cooling_layout.setObjectName(u"cooling_layout")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.cooling_layout.addItem(self.horizontalSpacer_3)

        self.pump_label = QLabel(self.plc_groupbox)
        self.pump_label.setObjectName(u"pump_label")
        self.pump_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.cooling_layout.addWidget(self.pump_label)

        self.pump_indicator = KStatusIndicator(self.plc_groupbox)
        self.pump_indicator.setObjectName(u"pump_indicator")
        sizePolicy.setHeightForWidth(self.pump_indicator.sizePolicy().hasHeightForWidth())
        self.pump_indicator.setSizePolicy(sizePolicy)
        self.pump_indicator.setMinimumSize(QSize(20, 20))
        self.pump_indicator.setMaximumSize(QSize(20, 20))
        self.pump_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.cooling_layout.addWidget(self.pump_indicator)

        self.pump_checkbox = QCheckBox(self.plc_groupbox)
        self.pump_checkbox.setObjectName(u"pump_checkbox")

        self.cooling_layout.addWidget(self.pump_checkbox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.cooling_layout.addItem(self.horizontalSpacer)

        self.fan_label = QLabel(self.plc_groupbox)
        self.fan_label.setObjectName(u"fan_label")
        self.fan_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.cooling_layout.addWidget(self.fan_label)

        self.heatexchanger_fan_indicator = KStatusIndicator(self.plc_groupbox)
        self.heatexchanger_fan_indicator.setObjectName(u"heatexchanger_fan_indicator")
        sizePolicy.setHeightForWidth(self.heatexchanger_fan_indicator.sizePolicy().hasHeightForWidth())
        self.heatexchanger_fan_indicator.setSizePolicy(sizePolicy)
        self.heatexchanger_fan_indicator.setMinimumSize(QSize(20, 20))
        self.heatexchanger_fan_indicator.setMaximumSize(QSize(20, 20))
        self.heatexchanger_fan_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.cooling_layout.addWidget(self.heatexchanger_fan_indicator)

        self.heatexchanger_fan_checkbox = QCheckBox(self.plc_groupbox)
        self.heatexchanger_fan_checkbox.setObjectName(u"heatexchanger_fan_checkbox")

        self.cooling_layout.addWidget(self.heatexchanger_fan_checkbox)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.cooling_layout.addItem(self.horizontalSpacer_2)

        self.heater_label = QLabel(self.plc_groupbox)
        self.heater_label.setObjectName(u"heater_label")
        self.heater_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.cooling_layout.addWidget(self.heater_label)

        self.heater_indicator = KStatusIndicator(self.plc_groupbox)
        self.heater_indicator.setObjectName(u"heater_indicator")
        sizePolicy.setHeightForWidth(self.heater_indicator.sizePolicy().hasHeightForWidth())
        self.heater_indicator.setSizePolicy(sizePolicy)
        self.heater_indicator.setMinimumSize(QSize(20, 20))
        self.heater_indicator.setMaximumSize(QSize(20, 20))
        self.heater_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.cooling_layout.addWidget(self.heater_indicator)

        self.heater_checkbox = QCheckBox(self.plc_groupbox)
        self.heater_checkbox.setObjectName(u"heater_checkbox")

        self.cooling_layout.addWidget(self.heater_checkbox)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.cooling_layout.addItem(self.horizontalSpacer_5)


        self.gridLayout_4.addLayout(self.cooling_layout, 13, 1, 1, 5)

        self.shutter_combobox = QComboBox(self.plc_groupbox)
        self.shutter_combobox.setObjectName(u"shutter_combobox")

        self.gridLayout_4.addWidget(self.shutter_combobox, 0, 2, 1, 1)

        self.filterwheel_indicator = KStatusIndicator(self.plc_groupbox)
        self.filterwheel_indicator.setObjectName(u"filterwheel_indicator")
        sizePolicy.setHeightForWidth(self.filterwheel_indicator.sizePolicy().hasHeightForWidth())
        self.filterwheel_indicator.setSizePolicy(sizePolicy)
        self.filterwheel_indicator.setMinimumSize(QSize(20, 20))
        self.filterwheel_indicator.setMaximumSize(QSize(20, 20))
        self.filterwheel_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.filterwheel_indicator, 5, 1, 1, 1)

        self.calibunit_tungsten_button = QPushButton(self.plc_groupbox)
        self.calibunit_tungsten_button.setObjectName(u"calibunit_tungsten_button")

        self.gridLayout_4.addWidget(self.calibunit_tungsten_button, 2, 5, 1, 1)

        self.frame_2 = QFrame(self.plc_groupbox)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.HLine)
        self.frame_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_4.addWidget(self.frame_2, 12, 0, 1, 6)

        self.adc2_indicator = KStatusIndicator(self.plc_groupbox)
        self.adc2_indicator.setObjectName(u"adc2_indicator")
        sizePolicy.setHeightForWidth(self.adc2_indicator.sizePolicy().hasHeightForWidth())
        self.adc2_indicator.setSizePolicy(sizePolicy)
        self.adc2_indicator.setMinimumSize(QSize(20, 20))
        self.adc2_indicator.setMaximumSize(QSize(20, 20))
        self.adc2_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.adc2_indicator, 7, 1, 1, 1)

        self.cooling_label = QLabel(self.plc_groupbox)
        self.cooling_label.setObjectName(u"cooling_label")
        self.cooling_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.cooling_label, 13, 0, 1, 1)

        self.flipmirror_indicator = KStatusIndicator(self.plc_groupbox)
        self.flipmirror_indicator.setObjectName(u"flipmirror_indicator")
        sizePolicy.setHeightForWidth(self.flipmirror_indicator.sizePolicy().hasHeightForWidth())
        self.flipmirror_indicator.setSizePolicy(sizePolicy)
        self.flipmirror_indicator.setMinimumSize(QSize(20, 20))
        self.flipmirror_indicator.setMaximumSize(QSize(20, 20))
        self.flipmirror_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.flipmirror_indicator, 1, 1, 1, 1)

        self.adc_offset_label = QLabel(self.plc_groupbox)
        self.adc_offset_label.setObjectName(u"adc_offset_label")
        self.adc_offset_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.adc_offset_label, 9, 0, 1, 1)

        self.adc_angle_spinbox = KNaNDoubleSpinbox(self.plc_groupbox)
        self.adc_angle_spinbox.setObjectName(u"adc_angle_spinbox")
        self.adc_angle_spinbox.setKeyboardTracking(False)
        self.adc_angle_spinbox.setMinimum(-360.000000000000000)
        self.adc_angle_spinbox.setMaximum(360.000000000000000)
        self.adc_angle_spinbox.setSingleStep(0.100000000000000)

        self.gridLayout_4.addWidget(self.adc_angle_spinbox, 8, 2, 1, 1)

        self.adc_offset_spinbox = KNaNDoubleSpinbox(self.plc_groupbox)
        self.adc_offset_spinbox.setObjectName(u"adc_offset_spinbox")
        self.adc_offset_spinbox.setKeyboardTracking(False)
        self.adc_offset_spinbox.setMinimum(-360.000000000000000)
        self.adc_offset_spinbox.setMaximum(360.000000000000000)
        self.adc_offset_spinbox.setSingleStep(0.100000000000000)

        self.gridLayout_4.addWidget(self.adc_offset_spinbox, 9, 2, 1, 1)

        self.adc_zero_disp_button = QPushButton(self.plc_groupbox)
        self.adc_zero_disp_button.setObjectName(u"adc_zero_disp_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.adc_zero_disp_button.sizePolicy().hasHeightForWidth())
        self.adc_zero_disp_button.setSizePolicy(sizePolicy1)

        self.gridLayout_4.addWidget(self.adc_zero_disp_button, 6, 4, 4, 1)

        self.adc_max_disp_button = QPushButton(self.plc_groupbox)
        self.adc_max_disp_button.setObjectName(u"adc_max_disp_button")
        sizePolicy1.setHeightForWidth(self.adc_max_disp_button.sizePolicy().hasHeightForWidth())
        self.adc_max_disp_button.setSizePolicy(sizePolicy1)

        self.gridLayout_4.addWidget(self.adc_max_disp_button, 6, 5, 4, 1)

        self.lamps_off_button = QPushButton(self.plc_groupbox)
        self.lamps_off_button.setObjectName(u"lamps_off_button")
        sizePolicy1.setHeightForWidth(self.lamps_off_button.sizePolicy().hasHeightForWidth())
        self.lamps_off_button.setSizePolicy(sizePolicy1)

        self.gridLayout_4.addWidget(self.lamps_off_button, 3, 4, 2, 2)

        self.label = QLabel(self.plc_groupbox)
        self.label.setObjectName(u"label")
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.gridLayout_4.addWidget(self.label, 5, 4, 1, 2)

        self.gridLayout_4.setColumnStretch(2, 1)
        self.gridLayout_4.setColumnStretch(3, 1)
        self.gridLayout_4.setColumnStretch(4, 1)

        self.left_pane_layout.addWidget(self.plc_groupbox)

        self.services_groupbox = QGroupBox(EngineeringWidget)
        self.services_groupbox.setObjectName(u"services_groupbox")
        self.verticalLayout_2 = QVBoxLayout(self.services_groupbox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.services_layout = QGridLayout()
        self.services_layout.setObjectName(u"services_layout")

        self.verticalLayout_2.addLayout(self.services_layout)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_7)


        self.left_pane_layout.addWidget(self.services_groupbox)

        self.calibration_poses_groupbox = QGroupBox(EngineeringWidget)
        self.calibration_poses_groupbox.setObjectName(u"calibration_poses_groupbox")
        self.verticalLayout_4 = QVBoxLayout(self.calibration_poses_groupbox)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.calibration_poses_button = QPushButton(self.calibration_poses_groupbox)
        self.calibration_poses_button.setObjectName(u"calibration_poses_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/calibration-poses.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.calibration_poses_button.setIcon(icon)

        self.verticalLayout_4.addWidget(self.calibration_poses_button)


        self.left_pane_layout.addWidget(self.calibration_poses_groupbox)


        self.horizontalLayout_3.addLayout(self.left_pane_layout)

        self.middle_pane_layout = QVBoxLayout()
        self.middle_pane_layout.setObjectName(u"middle_pane_layout")
        self.camera_groupbox = QGroupBox(EngineeringWidget)
        self.camera_groupbox.setObjectName(u"camera_groupbox")
        self.formLayout_2 = QFormLayout(self.camera_groupbox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.camera_status_layout = QHBoxLayout()
        self.camera_status_layout.setObjectName(u"camera_status_layout")
        self.camera_status_indicator = KStatusIndicator(self.camera_groupbox)
        self.camera_status_indicator.setObjectName(u"camera_status_indicator")
        sizePolicy.setHeightForWidth(self.camera_status_indicator.sizePolicy().hasHeightForWidth())
        self.camera_status_indicator.setSizePolicy(sizePolicy)
        self.camera_status_indicator.setMinimumSize(QSize(20, 20))
        self.camera_status_indicator.setMaximumSize(QSize(20, 20))
        self.camera_status_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.camera_status_layout.addWidget(self.camera_status_indicator)

        self.camera_status_lineedit = QLineEdit(self.camera_groupbox)
        self.camera_status_lineedit.setObjectName(u"camera_status_lineedit")
        self.camera_status_lineedit.setReadOnly(True)

        self.camera_status_layout.addWidget(self.camera_status_lineedit)


        self.formLayout_2.setLayout(0, QFormLayout.FieldRole, self.camera_status_layout)

        self.camera_exposure_time_label = QLabel(self.camera_groupbox)
        self.camera_exposure_time_label.setObjectName(u"camera_exposure_time_label")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.camera_exposure_time_label)

        self.camera_exposure_time_spinbox = KNaNDoubleSpinbox(self.camera_groupbox)
        self.camera_exposure_time_spinbox.setObjectName(u"camera_exposure_time_spinbox")
        self.camera_exposure_time_spinbox.setKeyboardTracking(False)
        self.camera_exposure_time_spinbox.setDecimals(3)
        self.camera_exposure_time_spinbox.setMinimum(0.001000000000000)
        self.camera_exposure_time_spinbox.setMaximum(99999999.000000000000000)
        self.camera_exposure_time_spinbox.setValue(1.000000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.camera_exposure_time_spinbox)

        self.camera_remaining_time_label = QLabel(self.camera_groupbox)
        self.camera_remaining_time_label.setObjectName(u"camera_remaining_time_label")

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

        self.camera_frames_label = QLabel(self.camera_groupbox)
        self.camera_frames_label.setObjectName(u"camera_frames_label")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.camera_frames_label)

        self.camera_frames_spinbox = QSpinBox(self.camera_groupbox)
        self.camera_frames_spinbox.setObjectName(u"camera_frames_spinbox")
        self.camera_frames_spinbox.setKeyboardTracking(False)
        self.camera_frames_spinbox.setMinimum(1)
        self.camera_frames_spinbox.setMaximum(9999)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.camera_frames_spinbox)

        self.camera_remaining_frames_label = QLabel(self.camera_groupbox)
        self.camera_remaining_frames_label.setObjectName(u"camera_remaining_frames_label")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.camera_remaining_frames_label)

        self.camera_remaining_frames_spinbox = QSpinBox(self.camera_groupbox)
        self.camera_remaining_frames_spinbox.setObjectName(u"camera_remaining_frames_spinbox")
        self.camera_remaining_frames_spinbox.setReadOnly(True)
        self.camera_remaining_frames_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.camera_remaining_frames_spinbox.setKeyboardTracking(False)
        self.camera_remaining_frames_spinbox.setMinimum(-1)
        self.camera_remaining_frames_spinbox.setMaximum(9999)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.camera_remaining_frames_spinbox)

        self.camera_roi_label = QLabel(self.camera_groupbox)
        self.camera_roi_label.setObjectName(u"camera_roi_label")

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.camera_roi_label)

        self.camera_roi_spinbox = QSpinBox(self.camera_groupbox)
        self.camera_roi_spinbox.setObjectName(u"camera_roi_spinbox")
        self.camera_roi_spinbox.setKeyboardTracking(False)
        self.camera_roi_spinbox.setMinimum(1)
        self.camera_roi_spinbox.setMaximum(1024)
        self.camera_roi_spinbox.setSingleStep(2)
        self.camera_roi_spinbox.setValue(1024)

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.camera_roi_spinbox)

        self.camera_new_image_button = QPushButton(self.camera_groupbox)
        self.camera_new_image_button.setObjectName(u"camera_new_image_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/insert-image.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.camera_new_image_button.setIcon(icon1)

        self.formLayout_2.setWidget(6, QFormLayout.SpanningRole, self.camera_new_image_button)

        self.camera_cancel_button = QPushButton(self.camera_groupbox)
        self.camera_cancel_button.setObjectName(u"camera_cancel_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/dialog-cancel.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.camera_cancel_button.setIcon(icon2)

        self.formLayout_2.setWidget(7, QFormLayout.SpanningRole, self.camera_cancel_button)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_2.setItem(8, QFormLayout.SpanningRole, self.verticalSpacer_3)

        self.camera_status_label = QLabel(self.camera_groupbox)
        self.camera_status_label.setObjectName(u"camera_status_label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.camera_status_label)


        self.middle_pane_layout.addWidget(self.camera_groupbox)

        self.wfs_groupbox = QGroupBox(EngineeringWidget)
        self.wfs_groupbox.setObjectName(u"wfs_groupbox")
        self.gridLayout_6 = QGridLayout(self.wfs_groupbox)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.wfs_acquisition_start_button = QPushButton(self.wfs_groupbox)
        self.wfs_acquisition_start_button.setObjectName(u"wfs_acquisition_start_button")
        icon3 = QIcon()
        icon3.addFile(u":/assets/icons/media-playback-start.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.wfs_acquisition_start_button.setIcon(icon3)

        self.gridLayout_6.addWidget(self.wfs_acquisition_start_button, 0, 2, 1, 1)

        self.wfs_acquisition_indicator = KStatusIndicator(self.wfs_groupbox)
        self.wfs_acquisition_indicator.setObjectName(u"wfs_acquisition_indicator")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.wfs_acquisition_indicator.sizePolicy().hasHeightForWidth())
        self.wfs_acquisition_indicator.setSizePolicy(sizePolicy2)
        self.wfs_acquisition_indicator.setMinimumSize(QSize(20, 20))
        self.wfs_acquisition_indicator.setMaximumSize(QSize(20, 20))
        self.wfs_acquisition_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_6.addWidget(self.wfs_acquisition_indicator, 0, 1, 1, 1)

        self.wfs_acquisition_label = QLabel(self.wfs_groupbox)
        self.wfs_acquisition_label.setObjectName(u"wfs_acquisition_label")
        self.wfs_acquisition_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_6.addWidget(self.wfs_acquisition_label, 0, 0, 1, 1)

        self.wfs_acquisition_stop_button = QPushButton(self.wfs_groupbox)
        self.wfs_acquisition_stop_button.setObjectName(u"wfs_acquisition_stop_button")
        icon4 = QIcon()
        icon4.addFile(u":/assets/icons/media-playback-stop.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.wfs_acquisition_stop_button.setIcon(icon4)

        self.gridLayout_6.addWidget(self.wfs_acquisition_stop_button, 0, 3, 1, 1)

        self.verticalSpacer_6 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_6.addItem(self.verticalSpacer_6, 1, 0, 1, 4)

        self.gridLayout_6.setColumnStretch(2, 1)
        self.gridLayout_6.setColumnStretch(3, 1)

        self.middle_pane_layout.addWidget(self.wfs_groupbox)

        self.dm_groupbox = QGroupBox(EngineeringWidget)
        self.dm_groupbox.setObjectName(u"dm_groupbox")
        self.gridLayout_2 = QGridLayout(self.dm_groupbox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.dm_on_button = QPushButton(self.dm_groupbox)
        self.dm_on_button.setObjectName(u"dm_on_button")
        icon5 = QIcon()
        icon5.addFile(u":/assets/icons/system-shutdown.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.dm_on_button.setIcon(icon5)

        self.gridLayout_2.addWidget(self.dm_on_button, 0, 0, 1, 1)

        self.dm_off_button = QPushButton(self.dm_groupbox)
        self.dm_off_button.setObjectName(u"dm_off_button")
        self.dm_off_button.setIcon(icon5)

        self.gridLayout_2.addWidget(self.dm_off_button, 0, 1, 1, 1)

        self.dm_channels_button = QPushButton(self.dm_groupbox)
        self.dm_channels_button.setObjectName(u"dm_channels_button")
        icon6 = QIcon()
        icon6.addFile(u":/assets/icons/vcs-merge.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.dm_channels_button.setIcon(icon6)

        self.gridLayout_2.addWidget(self.dm_channels_button, 1, 0, 1, 2)

        self.dm_calibration_button = QPushButton(self.dm_groupbox)
        self.dm_calibration_button.setObjectName(u"dm_calibration_button")
        icon7 = QIcon()
        icon7.addFile(u":/assets/icons/pattern.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.dm_calibration_button.setIcon(icon7)

        self.gridLayout_2.addWidget(self.dm_calibration_button, 2, 0, 1, 2)

        self.dm_direct_control_button = QPushButton(self.dm_groupbox)
        self.dm_direct_control_button.setObjectName(u"dm_direct_control_button")
        icon8 = QIcon()
        icon8.addFile(u":/assets/icons/grid-rectangular.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.dm_direct_control_button.setIcon(icon8)

        self.gridLayout_2.addWidget(self.dm_direct_control_button, 3, 0, 1, 2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer_2, 4, 0, 1, 2)


        self.middle_pane_layout.addWidget(self.dm_groupbox)

        self.ttm_groupbox = QGroupBox(EngineeringWidget)
        self.ttm_groupbox.setObjectName(u"ttm_groupbox")
        self.verticalLayout_3 = QVBoxLayout(self.ttm_groupbox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.ttm_channels_button = QPushButton(self.ttm_groupbox)
        self.ttm_channels_button.setObjectName(u"ttm_channels_button")
        self.ttm_channels_button.setIcon(icon6)

        self.verticalLayout_3.addWidget(self.ttm_channels_button)

        self.ttm_calibration_button = QPushButton(self.ttm_groupbox)
        self.ttm_calibration_button.setObjectName(u"ttm_calibration_button")
        self.ttm_calibration_button.setIcon(icon7)

        self.verticalLayout_3.addWidget(self.ttm_calibration_button)

        self.ttm_direct_control_button = QPushButton(self.ttm_groupbox)
        self.ttm_direct_control_button.setObjectName(u"ttm_direct_control_button")
        icon9 = QIcon()
        icon9.addFile(u":/assets/icons/settings-configure.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.ttm_direct_control_button.setIcon(icon9)

        self.verticalLayout_3.addWidget(self.ttm_direct_control_button)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_5)


        self.middle_pane_layout.addWidget(self.ttm_groupbox)

        self.centering_groupbox = QGroupBox(EngineeringWidget)
        self.centering_groupbox.setObjectName(u"centering_groupbox")
        self.gridLayout_7 = QGridLayout(self.centering_groupbox)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.centering_star_button = QPushButton(self.centering_groupbox)
        self.centering_star_button.setObjectName(u"centering_star_button")
        icon10 = QIcon()
        icon10.addFile(u":/assets/icons/crosshairs.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_star_button.setIcon(icon10)

        self.gridLayout_7.addWidget(self.centering_star_button, 0, 0, 1, 1)

        self.centering_laser_button = QPushButton(self.centering_groupbox)
        self.centering_laser_button.setObjectName(u"centering_laser_button")
        self.centering_laser_button.setIcon(icon10)

        self.gridLayout_7.addWidget(self.centering_laser_button, 0, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer_4, 2, 0, 1, 2)

        self.centering_spiral_search_button = QPushButton(self.centering_groupbox)
        self.centering_spiral_search_button.setObjectName(u"centering_spiral_search_button")
        icon11 = QIcon()
        icon11.addFile(u":/assets/icons/spiral-shape.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_spiral_search_button.setIcon(icon11)

        self.gridLayout_7.addWidget(self.centering_spiral_search_button, 1, 0, 1, 1)

        self.centering_spiral_search_window_button = QPushButton(self.centering_groupbox)
        self.centering_spiral_search_window_button.setObjectName(u"centering_spiral_search_window_button")
        self.centering_spiral_search_window_button.setIcon(icon11)

        self.gridLayout_7.addWidget(self.centering_spiral_search_window_button, 1, 1, 1, 1)


        self.middle_pane_layout.addWidget(self.centering_groupbox)

        self.focusing_groupbox = QGroupBox(EngineeringWidget)
        self.focusing_groupbox.setObjectName(u"focusing_groupbox")
        self.gridLayout_5 = QGridLayout(self.focusing_groupbox)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.focusing_open_focus_sequence_button = QPushButton(self.focusing_groupbox)
        self.focusing_open_focus_sequence_button.setObjectName(u"focusing_open_focus_sequence_button")
        icon12 = QIcon()
        icon12.addFile(u":/assets/icons/document-open.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.focusing_open_focus_sequence_button.setIcon(icon12)

        self.gridLayout_5.addWidget(self.focusing_open_focus_sequence_button, 1, 1, 1, 1)

        self.verticalSpacer_8 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_8, 2, 0, 1, 2)

        self.focusing_autofocus_button = QPushButton(self.focusing_groupbox)
        self.focusing_autofocus_button.setObjectName(u"focusing_autofocus_button")
        icon13 = QIcon()
        icon13.addFile(u":/assets/icons/tools-wizard.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.focusing_autofocus_button.setIcon(icon13)

        self.gridLayout_5.addWidget(self.focusing_autofocus_button, 1, 0, 1, 1)

        self.focusing_focus_sequence_button = QPushButton(self.focusing_groupbox)
        self.focusing_focus_sequence_button.setObjectName(u"focusing_focus_sequence_button")
        icon14 = QIcon()
        icon14.addFile(u":/assets/icons/focus.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.focusing_focus_sequence_button.setIcon(icon14)

        self.gridLayout_5.addWidget(self.focusing_focus_sequence_button, 0, 0, 1, 1)

        self.focusing_focus_sequence_window_button = QPushButton(self.focusing_groupbox)
        self.focusing_focus_sequence_window_button.setObjectName(u"focusing_focus_sequence_window_button")
        self.focusing_focus_sequence_window_button.setIcon(icon14)

        self.gridLayout_5.addWidget(self.focusing_focus_sequence_window_button, 0, 1, 1, 1)


        self.middle_pane_layout.addWidget(self.focusing_groupbox)


        self.horizontalLayout_3.addLayout(self.middle_pane_layout)

        self.right_pane_layout = QGridLayout()
        self.right_pane_layout.setObjectName(u"right_pane_layout")
        self.stream_groupbox = QGroupBox(EngineeringWidget)
        self.stream_groupbox.setObjectName(u"stream_groupbox")
        self.verticalLayout_7 = QVBoxLayout(self.stream_groupbox)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.stream_layout = QGridLayout()
        self.stream_layout.setObjectName(u"stream_layout")
        self.stream_status_label = QLabel(self.stream_groupbox)
        self.stream_status_label.setObjectName(u"stream_status_label")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stream_status_label.sizePolicy().hasHeightForWidth())
        self.stream_status_label.setSizePolicy(sizePolicy3)
        font = QFont()
        font.setBold(True)
        self.stream_status_label.setFont(font)

        self.stream_layout.addWidget(self.stream_status_label, 0, 3, 1, 1)

        self.shm_name_label = QLabel(self.stream_groupbox)
        self.shm_name_label.setObjectName(u"shm_name_label")
        self.shm_name_label.setFont(font)

        self.stream_layout.addWidget(self.shm_name_label, 0, 0, 1, 1)

        self.stream_size_label = QLabel(self.stream_groupbox)
        self.stream_size_label.setObjectName(u"stream_size_label")
        self.stream_size_label.setFont(font)

        self.stream_layout.addWidget(self.stream_size_label, 0, 1, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.stream_framerate_label = QLabel(self.stream_groupbox)
        self.stream_framerate_label.setObjectName(u"stream_framerate_label")
        self.stream_framerate_label.setFont(font)

        self.stream_layout.addWidget(self.stream_framerate_label, 0, 2, 1, 1, Qt.AlignmentFlag.AlignRight)


        self.verticalLayout_7.addLayout(self.stream_layout)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_10)

        self.milk_streamCTRL_label = QLabel(self.stream_groupbox)
        self.milk_streamCTRL_label.setObjectName(u"milk_streamCTRL_label")
        self.milk_streamCTRL_label.setWordWrap(True)

        self.verticalLayout_7.addWidget(self.milk_streamCTRL_label)


        self.right_pane_layout.addWidget(self.stream_groupbox, 1, 1, 1, 1)

        self.camstack_groupbox = QGroupBox(EngineeringWidget)
        self.camstack_groupbox.setObjectName(u"camstack_groupbox")
        self.gridLayout = QGridLayout(self.camstack_groupbox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_9, 0, 1, 1, 1)

        self.camstack_layout = QGridLayout()
        self.camstack_layout.setObjectName(u"camstack_layout")
        self.camstack_proc_label = QLabel(self.camstack_groupbox)
        self.camstack_proc_label.setObjectName(u"camstack_proc_label")
        self.camstack_proc_label.setFont(font)

        self.camstack_layout.addWidget(self.camstack_proc_label, 0, 2, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.camstack_tmux_label = QLabel(self.camstack_groupbox)
        self.camstack_tmux_label.setObjectName(u"camstack_tmux_label")
        self.camstack_tmux_label.setFont(font)

        self.camstack_layout.addWidget(self.camstack_tmux_label, 0, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.kalaocamctrl_label = QLabel(self.camstack_groupbox)
        self.kalaocamctrl_label.setObjectName(u"kalaocamctrl_label")

        self.camstack_layout.addWidget(self.kalaocamctrl_label, 1, 0, 1, 1)

        self.kalaocamctrl_proc_indicator = KStatusIndicator(self.camstack_groupbox)
        self.kalaocamctrl_proc_indicator.setObjectName(u"kalaocamctrl_proc_indicator")
        sizePolicy.setHeightForWidth(self.kalaocamctrl_proc_indicator.sizePolicy().hasHeightForWidth())
        self.kalaocamctrl_proc_indicator.setSizePolicy(sizePolicy)
        self.kalaocamctrl_proc_indicator.setMinimumSize(QSize(20, 20))
        self.kalaocamctrl_proc_indicator.setMaximumSize(QSize(20, 20))
        self.kalaocamctrl_proc_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.camstack_layout.addWidget(self.kalaocamctrl_proc_indicator, 1, 2, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.kalaocamctrl_tmux_indicator = KStatusIndicator(self.camstack_groupbox)
        self.kalaocamctrl_tmux_indicator.setObjectName(u"kalaocamctrl_tmux_indicator")
        sizePolicy.setHeightForWidth(self.kalaocamctrl_tmux_indicator.sizePolicy().hasHeightForWidth())
        self.kalaocamctrl_tmux_indicator.setSizePolicy(sizePolicy)
        self.kalaocamctrl_tmux_indicator.setMinimumSize(QSize(20, 20))
        self.kalaocamctrl_tmux_indicator.setMaximumSize(QSize(20, 20))
        self.kalaocamctrl_tmux_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.camstack_layout.addWidget(self.kalaocamctrl_tmux_indicator, 1, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.camstack_name_label = QLabel(self.camstack_groupbox)
        self.camstack_name_label.setObjectName(u"camstack_name_label")
        self.camstack_name_label.setFont(font)

        self.camstack_layout.addWidget(self.camstack_name_label, 0, 0, 1, 1)

        self.nuvufgrab_label = QLabel(self.camstack_groupbox)
        self.nuvufgrab_label.setObjectName(u"nuvufgrab_label")

        self.camstack_layout.addWidget(self.nuvufgrab_label, 2, 0, 1, 1)

        self.nuvufgrab_tmux_indicator = KStatusIndicator(self.camstack_groupbox)
        self.nuvufgrab_tmux_indicator.setObjectName(u"nuvufgrab_tmux_indicator")
        sizePolicy.setHeightForWidth(self.nuvufgrab_tmux_indicator.sizePolicy().hasHeightForWidth())
        self.nuvufgrab_tmux_indicator.setSizePolicy(sizePolicy)
        self.nuvufgrab_tmux_indicator.setMinimumSize(QSize(20, 20))
        self.nuvufgrab_tmux_indicator.setMaximumSize(QSize(20, 20))
        self.nuvufgrab_tmux_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.camstack_layout.addWidget(self.nuvufgrab_tmux_indicator, 2, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.nuvufgrab_proc_indicator = KStatusIndicator(self.camstack_groupbox)
        self.nuvufgrab_proc_indicator.setObjectName(u"nuvufgrab_proc_indicator")
        sizePolicy.setHeightForWidth(self.nuvufgrab_proc_indicator.sizePolicy().hasHeightForWidth())
        self.nuvufgrab_proc_indicator.setSizePolicy(sizePolicy)
        self.nuvufgrab_proc_indicator.setMinimumSize(QSize(20, 20))
        self.nuvufgrab_proc_indicator.setMaximumSize(QSize(20, 20))
        self.nuvufgrab_proc_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.camstack_layout.addWidget(self.nuvufgrab_proc_indicator, 2, 2, 1, 1, Qt.AlignmentFlag.AlignHCenter)


        self.gridLayout.addLayout(self.camstack_layout, 0, 0, 1, 1)

        self.verticalSpacer_11 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_11, 1, 0, 1, 2)


        self.right_pane_layout.addWidget(self.camstack_groupbox, 0, 1, 1, 1)

        self.ippower_groupbox = QGroupBox(EngineeringWidget)
        self.ippower_groupbox.setObjectName(u"ippower_groupbox")
        self.gridLayout_3 = QGridLayout(self.ippower_groupbox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.ippower_bench_label = QLabel(self.ippower_groupbox)
        self.ippower_bench_label.setObjectName(u"ippower_bench_label")
        self.ippower_bench_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.ippower_bench_label, 1, 0, 1, 1)

        self.ippower_rtc_on_button = QPushButton(self.ippower_groupbox)
        self.ippower_rtc_on_button.setObjectName(u"ippower_rtc_on_button")
        self.ippower_rtc_on_button.setEnabled(False)
        self.ippower_rtc_on_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_rtc_on_button, 0, 2, 1, 1)

        self.ippower_dm_indicator = KStatusIndicator(self.ippower_groupbox)
        self.ippower_dm_indicator.setObjectName(u"ippower_dm_indicator")
        sizePolicy2.setHeightForWidth(self.ippower_dm_indicator.sizePolicy().hasHeightForWidth())
        self.ippower_dm_indicator.setSizePolicy(sizePolicy2)
        self.ippower_dm_indicator.setMinimumSize(QSize(20, 20))
        self.ippower_dm_indicator.setMaximumSize(QSize(20, 20))
        self.ippower_dm_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_3.addWidget(self.ippower_dm_indicator, 2, 1, 1, 1)

        self.ippower_bench_indicator = KStatusIndicator(self.ippower_groupbox)
        self.ippower_bench_indicator.setObjectName(u"ippower_bench_indicator")
        sizePolicy2.setHeightForWidth(self.ippower_bench_indicator.sizePolicy().hasHeightForWidth())
        self.ippower_bench_indicator.setSizePolicy(sizePolicy2)
        self.ippower_bench_indicator.setMinimumSize(QSize(20, 20))
        self.ippower_bench_indicator.setMaximumSize(QSize(20, 20))
        self.ippower_bench_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_3.addWidget(self.ippower_bench_indicator, 1, 1, 1, 1)

        self.ippower_dm_label = QLabel(self.ippower_groupbox)
        self.ippower_dm_label.setObjectName(u"ippower_dm_label")
        self.ippower_dm_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.ippower_dm_label, 2, 0, 1, 1)

        self.ippower_rtc_indicator = KStatusIndicator(self.ippower_groupbox)
        self.ippower_rtc_indicator.setObjectName(u"ippower_rtc_indicator")
        sizePolicy2.setHeightForWidth(self.ippower_rtc_indicator.sizePolicy().hasHeightForWidth())
        self.ippower_rtc_indicator.setSizePolicy(sizePolicy2)
        self.ippower_rtc_indicator.setMinimumSize(QSize(20, 20))
        self.ippower_rtc_indicator.setMaximumSize(QSize(20, 20))
        self.ippower_rtc_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_3.addWidget(self.ippower_rtc_indicator, 0, 1, 1, 1)

        self.ippower_rtc_off_button = QPushButton(self.ippower_groupbox)
        self.ippower_rtc_off_button.setObjectName(u"ippower_rtc_off_button")
        self.ippower_rtc_off_button.setEnabled(False)
        self.ippower_rtc_off_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_rtc_off_button, 0, 3, 1, 1)

        self.ippower_bench_on_button = QPushButton(self.ippower_groupbox)
        self.ippower_bench_on_button.setObjectName(u"ippower_bench_on_button")
        self.ippower_bench_on_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_bench_on_button, 1, 2, 1, 1)

        self.ippower_dm_on_button = QPushButton(self.ippower_groupbox)
        self.ippower_dm_on_button.setObjectName(u"ippower_dm_on_button")
        self.ippower_dm_on_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_dm_on_button, 2, 2, 1, 1)

        self.ippower_bench_off_button = QPushButton(self.ippower_groupbox)
        self.ippower_bench_off_button.setObjectName(u"ippower_bench_off_button")
        self.ippower_bench_off_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_bench_off_button, 1, 3, 1, 1)

        self.ippower_dm_off_button = QPushButton(self.ippower_groupbox)
        self.ippower_dm_off_button.setObjectName(u"ippower_dm_off_button")
        self.ippower_dm_off_button.setIcon(icon5)

        self.gridLayout_3.addWidget(self.ippower_dm_off_button, 2, 3, 1, 1)

        self.ippower_rtc_label = QLabel(self.ippower_groupbox)
        self.ippower_rtc_label.setObjectName(u"ippower_rtc_label")
        self.ippower_rtc_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.ippower_rtc_label, 0, 0, 1, 1)

        self.gridLayout_3.setColumnStretch(2, 1)
        self.gridLayout_3.setColumnStretch(3, 1)

        self.right_pane_layout.addWidget(self.ippower_groupbox, 0, 0, 1, 1)

        self.modalstats_groupbox = QGroupBox(EngineeringWidget)
        self.modalstats_groupbox.setObjectName(u"modalstats_groupbox")
        self.verticalLayout_8 = QVBoxLayout(self.modalstats_groupbox)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.cacao_modalstatsTUI_label = QLabel(self.modalstats_groupbox)
        self.cacao_modalstatsTUI_label.setObjectName(u"cacao_modalstatsTUI_label")
        self.cacao_modalstatsTUI_label.setWordWrap(True)

        self.verticalLayout_8.addWidget(self.cacao_modalstatsTUI_label)


        self.right_pane_layout.addWidget(self.modalstats_groupbox, 2, 0, 1, 2)

        self.proc_groupbox = QGroupBox(EngineeringWidget)
        self.proc_groupbox.setObjectName(u"proc_groupbox")
        self.verticalLayout_5 = QVBoxLayout(self.proc_groupbox)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.proc_layout = QGridLayout()
        self.proc_layout.setObjectName(u"proc_layout")
        self.proc_run_label = QLabel(self.proc_groupbox)
        self.proc_run_label.setObjectName(u"proc_run_label")
        self.proc_run_label.setFont(font)

        self.proc_layout.addWidget(self.proc_run_label, 0, 3, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.proc_conf_label = QLabel(self.proc_groupbox)
        self.proc_conf_label.setObjectName(u"proc_conf_label")
        self.proc_conf_label.setFont(font)

        self.proc_layout.addWidget(self.proc_conf_label, 0, 2, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.proc_tmux_label = QLabel(self.proc_groupbox)
        self.proc_tmux_label.setObjectName(u"proc_tmux_label")
        self.proc_tmux_label.setFont(font)

        self.proc_layout.addWidget(self.proc_tmux_label, 0, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.proc_name_label = QLabel(self.proc_groupbox)
        self.proc_name_label.setObjectName(u"proc_name_label")
        self.proc_name_label.setFont(font)

        self.proc_layout.addWidget(self.proc_name_label, 0, 0, 1, 1)

        self.proc_layout.setColumnStretch(1, 1)
        self.proc_layout.setColumnStretch(2, 1)
        self.proc_layout.setColumnStretch(3, 1)

        self.verticalLayout_5.addLayout(self.proc_layout)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_9)

        self.milk_fpsCTRL_label = QLabel(self.proc_groupbox)
        self.milk_fpsCTRL_label.setObjectName(u"milk_fpsCTRL_label")
        self.milk_fpsCTRL_label.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.milk_fpsCTRL_label)


        self.right_pane_layout.addWidget(self.proc_groupbox, 1, 0, 1, 1)

        self.deadman_groupbox = QGroupBox(EngineeringWidget)
        self.deadman_groupbox.setObjectName(u"deadman_groupbox")
        self.horizontalLayout = QHBoxLayout(self.deadman_groupbox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.deadman_checkbox = QCheckBox(self.deadman_groupbox)
        self.deadman_checkbox.setObjectName(u"deadman_checkbox")

        self.horizontalLayout.addWidget(self.deadman_checkbox)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_7)

        self.deadman_label = KLabel(self.deadman_groupbox)
        self.deadman_label.setObjectName(u"deadman_label")

        self.horizontalLayout.addWidget(self.deadman_label)


        self.right_pane_layout.addWidget(self.deadman_groupbox, 3, 0, 1, 2)

        self.instrument_rtc_groupbox = QGroupBox(EngineeringWidget)
        self.instrument_rtc_groupbox.setObjectName(u"instrument_rtc_groupbox")
        self.horizontalLayout_4 = QHBoxLayout(self.instrument_rtc_groupbox)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.instrument_shutdown_sequence_button = QPushButton(self.instrument_rtc_groupbox)
        self.instrument_shutdown_sequence_button.setObjectName(u"instrument_shutdown_sequence_button")
        self.instrument_shutdown_sequence_button.setIcon(icon5)

        self.horizontalLayout_4.addWidget(self.instrument_shutdown_sequence_button)

        self.rtc_poweroff_button = QPushButton(self.instrument_rtc_groupbox)
        self.rtc_poweroff_button.setObjectName(u"rtc_poweroff_button")
        self.rtc_poweroff_button.setIcon(icon5)

        self.horizontalLayout_4.addWidget(self.rtc_poweroff_button)

        self.rtc_reboot_button = QPushButton(self.instrument_rtc_groupbox)
        self.rtc_reboot_button.setObjectName(u"rtc_reboot_button")
        icon15 = QIcon()
        icon15.addFile(u":/assets/icons/system-reboot.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.rtc_reboot_button.setIcon(icon15)

        self.horizontalLayout_4.addWidget(self.rtc_reboot_button)


        self.right_pane_layout.addWidget(self.instrument_rtc_groupbox, 4, 0, 1, 2)

        self.right_pane_layout.setRowStretch(1, 1)

        self.horizontalLayout_3.addLayout(self.right_pane_layout)

        self.horizontalLayout_3.setStretch(0, 3)
        self.horizontalLayout_3.setStretch(1, 2)
        self.horizontalLayout_3.setStretch(2, 2)

        self.retranslateUi(EngineeringWidget)

        QMetaObject.connectSlotsByName(EngineeringWidget)
    # setupUi

    def retranslateUi(self, EngineeringWidget):
        EngineeringWidget.setWindowTitle(QCoreApplication.translate("EngineeringWidget", u"Engineering - KalAO", None))
        self.plc_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"PLC (Beckhoff) / Misc. hardware", None))
        self.adc2_label.setText(QCoreApplication.translate("EngineeringWidget", u"ADC 2", None))
        self.adc1_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u"\u00b0", None))
        self.adc1_label.setText(QCoreApplication.translate("EngineeringWidget", u"ADC 1", None))
        self.laser_status_checkbox.setText("")
        self.laser_power_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" mW", None))
        self.shutter_label.setText(QCoreApplication.translate("EngineeringWidget", u"Shutter", None))
        self.calibunit_label.setText(QCoreApplication.translate("EngineeringWidget", u"Calibration Unit", None))
        self.calibunit_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" mm", None))
        self.filterwheel_label.setText(QCoreApplication.translate("EngineeringWidget", u"Filter Wheel", None))
        self.calibunit_laser_button.setText(QCoreApplication.translate("EngineeringWidget", u"Go to Laser position", None))
        self.flipmirror_label.setText(QCoreApplication.translate("EngineeringWidget", u"Flip Mirror", None))
        self.shutter_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Shutter", None))
        self.flipmirror_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Flip Mirror", None))
        self.calibunit_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Calibration Unit", None))
        self.filterwheel_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Filter Wheel", None))
        self.tungsten_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Tungsten", None))
        self.laser_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"Laser", None))
        self.adc1_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"ADC 1", None))
        self.adc2_init_button.setText(QCoreApplication.translate("EngineeringWidget", u"ADC 2", None))
        self.adc2_stop_button.setText(QCoreApplication.translate("EngineeringWidget", u"Stop", None))
        self.laser_label.setText(QCoreApplication.translate("EngineeringWidget", u"Laser", None))
        self.adc2_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u"\u00b0", None))
        self.tungsten_status_checkbox.setText("")
        self.tungsten_label.setText(QCoreApplication.translate("EngineeringWidget", u"Tungsten", None))
        self.adc1_stop_button.setText(QCoreApplication.translate("EngineeringWidget", u"Stop", None))
        self.calibunit_stop_button.setText(QCoreApplication.translate("EngineeringWidget", u"Stop", None))
        self.adc_angle_label.setText(QCoreApplication.translate("EngineeringWidget", u"ADC Angle", None))
        self.init_label.setText(QCoreApplication.translate("EngineeringWidget", u"Initialize", None))
        self.pump_label.setText(QCoreApplication.translate("EngineeringWidget", u"Pump", None))
        self.pump_checkbox.setText("")
        self.fan_label.setText(QCoreApplication.translate("EngineeringWidget", u"Heat Exchanger Fan", None))
        self.heatexchanger_fan_checkbox.setText("")
        self.heater_label.setText(QCoreApplication.translate("EngineeringWidget", u"Heater", None))
        self.heater_checkbox.setText("")
        self.calibunit_tungsten_button.setText(QCoreApplication.translate("EngineeringWidget", u"Go to Tungsten position", None))
        self.cooling_label.setText(QCoreApplication.translate("EngineeringWidget", u"Cooling", None))
        self.adc_offset_label.setText(QCoreApplication.translate("EngineeringWidget", u"ADC Offset", None))
        self.adc_angle_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u"\u00b0", None))
        self.adc_offset_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u"\u00b0", None))
        self.adc_zero_disp_button.setText(QCoreApplication.translate("EngineeringWidget", u"Set Zero dispersion", None))
        self.adc_max_disp_button.setText(QCoreApplication.translate("EngineeringWidget", u"Set Max dispersion", None))
        self.lamps_off_button.setText(QCoreApplication.translate("EngineeringWidget", u"Lamps Off", None))
        self.label.setText(QCoreApplication.translate("EngineeringWidget", u"<a href=\"https://gitlab.unige.ch/kalao/kalao-ics/-/wikis/Technical/Filters-and-Science-Camera\">Filter details here.</a>", None))
        self.services_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Services", None))
        self.calibration_poses_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Calibration Poses", None))
        self.calibration_poses_button.setText(QCoreApplication.translate("EngineeringWidget", u"Calibration poses ...", None))
        self.camera_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Science Camera (Finger Lakes Instrumentation)", None))
        self.camera_exposure_time_label.setText(QCoreApplication.translate("EngineeringWidget", u"Exposure time", None))
        self.camera_exposure_time_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" s", None))
        self.camera_remaining_time_label.setText(QCoreApplication.translate("EngineeringWidget", u"Remaining time", None))
        self.camera_remaining_time_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" s", None))
        self.camera_frames_label.setText(QCoreApplication.translate("EngineeringWidget", u"Frames", None))
        self.camera_frames_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" frames", None))
        self.camera_remaining_frames_label.setText(QCoreApplication.translate("EngineeringWidget", u"Remaining frames", None))
        self.camera_remaining_frames_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" frames", None))
        self.camera_roi_label.setText(QCoreApplication.translate("EngineeringWidget", u"Window size", None))
        self.camera_roi_spinbox.setSuffix(QCoreApplication.translate("EngineeringWidget", u" px", None))
        self.camera_new_image_button.setText(QCoreApplication.translate("EngineeringWidget", u"Take a new image", None))
        self.camera_cancel_button.setText(QCoreApplication.translate("EngineeringWidget", u"Cancel exposure", None))
        self.camera_status_label.setText(QCoreApplication.translate("EngineeringWidget", u"Status", None))
        self.wfs_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Wavefront Sensor (N\u00fcv\u00fc)", None))
        self.wfs_acquisition_start_button.setText(QCoreApplication.translate("EngineeringWidget", u"Start", None))
        self.wfs_acquisition_label.setText(QCoreApplication.translate("EngineeringWidget", u"Acquisition", None))
        self.wfs_acquisition_stop_button.setText(QCoreApplication.translate("EngineeringWidget", u"Stop", None))
        self.dm_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Deformable Mirror (Boston Micromachines Corporation)", None))
        self.dm_on_button.setText(QCoreApplication.translate("EngineeringWidget", u"On", None))
        self.dm_off_button.setText(QCoreApplication.translate("EngineeringWidget", u"Off", None))
        self.dm_channels_button.setText(QCoreApplication.translate("EngineeringWidget", u"Channels and commands ...", None))
        self.dm_calibration_button.setText(QCoreApplication.translate("EngineeringWidget", u"Calibration ...", None))
        self.dm_direct_control_button.setText(QCoreApplication.translate("EngineeringWidget", u"Direct control ...", None))
        self.ttm_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Tip-Tilt Mirror (Physik Instrumente)", None))
        self.ttm_channels_button.setText(QCoreApplication.translate("EngineeringWidget", u"Channels and commands ...", None))
        self.ttm_calibration_button.setText(QCoreApplication.translate("EngineeringWidget", u"Calibration ...", None))
        self.ttm_direct_control_button.setText(QCoreApplication.translate("EngineeringWidget", u"Direct control ...", None))
        self.centering_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Centering", None))
        self.centering_star_button.setText(QCoreApplication.translate("EngineeringWidget", u"Launch star centering", None))
        self.centering_laser_button.setText(QCoreApplication.translate("EngineeringWidget", u"Launch laser centering", None))
        self.centering_spiral_search_button.setText(QCoreApplication.translate("EngineeringWidget", u"Launch spiral search", None))
        self.centering_spiral_search_window_button.setText(QCoreApplication.translate("EngineeringWidget", u"Spiral search window ...", None))
        self.focusing_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Focusing", None))
        self.focusing_open_focus_sequence_button.setText(QCoreApplication.translate("EngineeringWidget", u"Open a focus sequence ...", None))
        self.focusing_autofocus_button.setText(QCoreApplication.translate("EngineeringWidget", u"Launch autofocus", None))
        self.focusing_focus_sequence_button.setText(QCoreApplication.translate("EngineeringWidget", u"Launch focus sequence", None))
        self.focusing_focus_sequence_window_button.setText(QCoreApplication.translate("EngineeringWidget", u"Focus sequence window...", None))
        self.stream_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"CACAO Streams", None))
        self.stream_status_label.setText("")
        self.shm_name_label.setText(QCoreApplication.translate("EngineeringWidget", u"Name", None))
        self.stream_size_label.setText(QCoreApplication.translate("EngineeringWidget", u"Size", None))
        self.stream_framerate_label.setText(QCoreApplication.translate("EngineeringWidget", u"Framerate", None))
        self.milk_streamCTRL_label.setText(QCoreApplication.translate("EngineeringWidget", u"Use <span style=\"font-weight: bold;\">milk-streamCTRL</span> for advanced control.", None))
        self.camstack_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Camstack", None))
        self.camstack_proc_label.setText(QCoreApplication.translate("EngineeringWidget", u"PROC", None))
        self.camstack_tmux_label.setText(QCoreApplication.translate("EngineeringWidget", u"TMUX", None))
        self.kalaocamctrl_label.setText(QCoreApplication.translate("EngineeringWidget", u"kalaocam_ctrl", None))
        self.camstack_name_label.setText(QCoreApplication.translate("EngineeringWidget", u"Name", None))
        self.nuvufgrab_label.setText(QCoreApplication.translate("EngineeringWidget", u"nuvu_fgrab", None))
        self.ippower_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"IPPower", None))
        self.ippower_bench_label.setText(QCoreApplication.translate("EngineeringWidget", u"Bench", None))
        self.ippower_rtc_on_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power on", None))
        self.ippower_dm_label.setText(QCoreApplication.translate("EngineeringWidget", u"DM", None))
        self.ippower_rtc_off_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power off", None))
        self.ippower_bench_on_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power on", None))
        self.ippower_dm_on_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power on", None))
        self.ippower_bench_off_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power off", None))
        self.ippower_dm_off_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power off", None))
        self.ippower_rtc_label.setText(QCoreApplication.translate("EngineeringWidget", u"RTC", None))
        self.modalstats_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"CACAO Modal stats", None))
        self.cacao_modalstatsTUI_label.setText(QCoreApplication.translate("EngineeringWidget", u"Use <span style=\"font-weight: bold;\">cacao-modalstatsTUI</span> to tune modal gains et check loops stability.", None))
        self.proc_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"CACAO Processes", None))
        self.proc_run_label.setText(QCoreApplication.translate("EngineeringWidget", u"RUN", None))
        self.proc_conf_label.setText(QCoreApplication.translate("EngineeringWidget", u"CONF", None))
        self.proc_tmux_label.setText(QCoreApplication.translate("EngineeringWidget", u"TMUX", None))
        self.proc_name_label.setText(QCoreApplication.translate("EngineeringWidget", u"Name", None))
        self.milk_fpsCTRL_label.setText(QCoreApplication.translate("EngineeringWidget", u"Use <span style=\"font-weight: bold;\">milk-fpsCTRL</span> and <span style=\"font-weight: bold;\">milk-procCTRL</span> for advanced control.", None))
        self.deadman_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Dead-man", None))
        self.deadman_checkbox.setText(QCoreApplication.translate("EngineeringWidget", u"Active", None))
        self.deadman_label.setText(QCoreApplication.translate("EngineeringWidget", u"Count: {count}, last update: {last}, next update: {next}", None))
        self.instrument_rtc_groupbox.setTitle(QCoreApplication.translate("EngineeringWidget", u"Instrument / Real-time Computer", None))
        self.instrument_shutdown_sequence_button.setText(QCoreApplication.translate("EngineeringWidget", u"Shutdown instrument", None))
        self.rtc_poweroff_button.setText(QCoreApplication.translate("EngineeringWidget", u"Power off RTC", None))
        self.rtc_reboot_button.setText(QCoreApplication.translate("EngineeringWidget", u"Reboot RTC", None))
    # retranslateUi

