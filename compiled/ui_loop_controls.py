# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'loop_controls.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KChartView, KDraggableChartView)

class Ui_LoopControlsWidget(object):
    def setupUi(self, LoopControlsWidget):
        if not LoopControlsWidget.objectName():
            LoopControlsWidget.setObjectName(u"LoopControlsWidget")
        LoopControlsWidget.resize(1555, 1056)
        self.horizontalLayout_2 = QHBoxLayout(LoopControlsWidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.controls_layout = QVBoxLayout()
        self.controls_layout.setObjectName(u"controls_layout")
        self.dmloop_groupbox = QGroupBox(LoopControlsWidget)
        self.dmloop_groupbox.setObjectName(u"dmloop_groupbox")
        self.dmloop_groupbox.setEnabled(False)
        self.formLayout_3 = QFormLayout(self.dmloop_groupbox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dmloop_on_label = QLabel(self.dmloop_groupbox)
        self.dmloop_on_label.setObjectName(u"dmloop_on_label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.dmloop_on_label)

        self.dmloop_on_checkbox = QCheckBox(self.dmloop_groupbox)
        self.dmloop_on_checkbox.setObjectName(u"dmloop_on_checkbox")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.dmloop_on_checkbox)

        self.dmloopgain_label = QLabel(self.dmloop_groupbox)
        self.dmloopgain_label.setObjectName(u"dmloopgain_label")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.dmloopgain_label)

        self.dmloop_gain_spinbox = QDoubleSpinBox(self.dmloop_groupbox)
        self.dmloop_gain_spinbox.setObjectName(u"dmloop_gain_spinbox")
        self.dmloop_gain_spinbox.setKeyboardTracking(False)
        self.dmloop_gain_spinbox.setDecimals(6)
        self.dmloop_gain_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.dmloop_gain_spinbox)

        self.dmloop_mult_spinbox = QDoubleSpinBox(self.dmloop_groupbox)
        self.dmloop_mult_spinbox.setObjectName(u"dmloop_mult_spinbox")
        self.dmloop_mult_spinbox.setKeyboardTracking(False)
        self.dmloop_mult_spinbox.setDecimals(6)
        self.dmloop_mult_spinbox.setMaximum(1.000000000000000)
        self.dmloop_mult_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(2, QFormLayout.FieldRole, self.dmloop_mult_spinbox)

        self.dmloop_mult_label = QLabel(self.dmloop_groupbox)
        self.dmloop_mult_label.setObjectName(u"dmloop_mult_label")

        self.formLayout_3.setWidget(2, QFormLayout.LabelRole, self.dmloop_mult_label)

        self.dmloop_limit_label = QLabel(self.dmloop_groupbox)
        self.dmloop_limit_label.setObjectName(u"dmloop_limit_label")

        self.formLayout_3.setWidget(3, QFormLayout.LabelRole, self.dmloop_limit_label)

        self.dmloop_limit_spinbox = QDoubleSpinBox(self.dmloop_groupbox)
        self.dmloop_limit_spinbox.setObjectName(u"dmloop_limit_spinbox")
        self.dmloop_limit_spinbox.setKeyboardTracking(False)
        self.dmloop_limit_spinbox.setDecimals(6)
        self.dmloop_limit_spinbox.setMaximum(999.990000000000009)
        self.dmloop_limit_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_3.setWidget(3, QFormLayout.FieldRole, self.dmloop_limit_spinbox)

        self.dmloop_zero_button = QPushButton(self.dmloop_groupbox)
        self.dmloop_zero_button.setObjectName(u"dmloop_zero_button")

        self.formLayout_3.setWidget(4, QFormLayout.SpanningRole, self.dmloop_zero_button)


        self.controls_layout.addWidget(self.dmloop_groupbox)

        self.ttmloop_groupbox = QGroupBox(LoopControlsWidget)
        self.ttmloop_groupbox.setObjectName(u"ttmloop_groupbox")
        self.ttmloop_groupbox.setEnabled(False)
        self.formLayout_4 = QFormLayout(self.ttmloop_groupbox)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.ttmloop_on_label = QLabel(self.ttmloop_groupbox)
        self.ttmloop_on_label.setObjectName(u"ttmloop_on_label")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.ttmloop_on_label)

        self.ttmloop_gain_label = QLabel(self.ttmloop_groupbox)
        self.ttmloop_gain_label.setObjectName(u"ttmloop_gain_label")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.ttmloop_gain_label)

        self.ttmloop_mult_label = QLabel(self.ttmloop_groupbox)
        self.ttmloop_mult_label.setObjectName(u"ttmloop_mult_label")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.ttmloop_mult_label)

        self.ttmloop_limit_label = QLabel(self.ttmloop_groupbox)
        self.ttmloop_limit_label.setObjectName(u"ttmloop_limit_label")

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.ttmloop_limit_label)

        self.ttmloop_on_checkbox = QCheckBox(self.ttmloop_groupbox)
        self.ttmloop_on_checkbox.setObjectName(u"ttmloop_on_checkbox")

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.ttmloop_on_checkbox)

        self.ttmloop_gain_spinbox = QDoubleSpinBox(self.ttmloop_groupbox)
        self.ttmloop_gain_spinbox.setObjectName(u"ttmloop_gain_spinbox")
        self.ttmloop_gain_spinbox.setKeyboardTracking(False)
        self.ttmloop_gain_spinbox.setDecimals(6)
        self.ttmloop_gain_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.ttmloop_gain_spinbox)

        self.ttmloop_mult_spinbox = QDoubleSpinBox(self.ttmloop_groupbox)
        self.ttmloop_mult_spinbox.setObjectName(u"ttmloop_mult_spinbox")
        self.ttmloop_mult_spinbox.setKeyboardTracking(False)
        self.ttmloop_mult_spinbox.setDecimals(6)
        self.ttmloop_mult_spinbox.setMaximum(1.000000000000000)
        self.ttmloop_mult_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.ttmloop_mult_spinbox)

        self.ttmloop_limit_spinbox = QDoubleSpinBox(self.ttmloop_groupbox)
        self.ttmloop_limit_spinbox.setObjectName(u"ttmloop_limit_spinbox")
        self.ttmloop_limit_spinbox.setKeyboardTracking(False)
        self.ttmloop_limit_spinbox.setDecimals(6)
        self.ttmloop_limit_spinbox.setMaximum(999.990000000000009)
        self.ttmloop_limit_spinbox.setSingleStep(0.010000000000000)

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.ttmloop_limit_spinbox)

        self.ttmloop_zero_button = QPushButton(self.ttmloop_groupbox)
        self.ttmloop_zero_button.setObjectName(u"ttmloop_zero_button")

        self.formLayout_4.setWidget(4, QFormLayout.SpanningRole, self.ttmloop_zero_button)


        self.controls_layout.addWidget(self.ttmloop_groupbox)

        self.wfs_groupbox = QGroupBox(LoopControlsWidget)
        self.wfs_groupbox.setObjectName(u"wfs_groupbox")
        self.wfs_groupbox.setEnabled(False)
        self.formLayout_2 = QFormLayout(self.wfs_groupbox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.wfs_emgain_label = QLabel(self.wfs_groupbox)
        self.wfs_emgain_label.setObjectName(u"wfs_emgain_label")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.wfs_emgain_label)

        self.wfs_emgain_spinbox = QSpinBox(self.wfs_groupbox)
        self.wfs_emgain_spinbox.setObjectName(u"wfs_emgain_spinbox")
        self.wfs_emgain_spinbox.setKeyboardTracking(False)
        self.wfs_emgain_spinbox.setMinimum(1)
        self.wfs_emgain_spinbox.setMaximum(1000)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.wfs_emgain_spinbox)

        self.wfs_exposuretime_label = QLabel(self.wfs_groupbox)
        self.wfs_exposuretime_label.setObjectName(u"wfs_exposuretime_label")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.wfs_exposuretime_label)

        self.wfs_exposuretime_spinbox = QDoubleSpinBox(self.wfs_groupbox)
        self.wfs_exposuretime_spinbox.setObjectName(u"wfs_exposuretime_spinbox")
        self.wfs_exposuretime_spinbox.setKeyboardTracking(False)
        self.wfs_exposuretime_spinbox.setDecimals(2)
        self.wfs_exposuretime_spinbox.setMaximum(1000.000000000000000)
        self.wfs_exposuretime_spinbox.setSingleStep(0.100000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.wfs_exposuretime_spinbox)

        self.wfs_autogain_label = QLabel(self.wfs_groupbox)
        self.wfs_autogain_label.setObjectName(u"wfs_autogain_label")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.wfs_autogain_label)

        self.wfs_autogain_checkbox = QCheckBox(self.wfs_groupbox)
        self.wfs_autogain_checkbox.setObjectName(u"wfs_autogain_checkbox")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.wfs_autogain_checkbox)

        self.wfs_autogain_setting_label = QLabel(self.wfs_groupbox)
        self.wfs_autogain_setting_label.setObjectName(u"wfs_autogain_setting_label")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.wfs_autogain_setting_label)

        self.wfs_autogain_setting_combobox = QComboBox(self.wfs_groupbox)
        self.wfs_autogain_setting_combobox.setObjectName(u"wfs_autogain_setting_combobox")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.wfs_autogain_setting_combobox)

        self.wfs_algorithm_label = QLabel(self.wfs_groupbox)
        self.wfs_algorithm_label.setObjectName(u"wfs_algorithm_label")

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.wfs_algorithm_label)

        self.wfs_algorithm_combobox = QComboBox(self.wfs_groupbox)
        self.wfs_algorithm_combobox.setObjectName(u"wfs_algorithm_combobox")
        self.wfs_algorithm_combobox.setEnabled(False)

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.wfs_algorithm_combobox)


        self.controls_layout.addWidget(self.wfs_groupbox)

        self.dm_groupbox = QGroupBox(LoopControlsWidget)
        self.dm_groupbox.setObjectName(u"dm_groupbox")
        self.dm_groupbox.setEnabled(False)
        self.formLayout_5 = QFormLayout(self.dm_groupbox)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.formLayout_5.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.dm_maxstroke_label = QLabel(self.dm_groupbox)
        self.dm_maxstroke_label.setObjectName(u"dm_maxstroke_label")

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.dm_maxstroke_label)

        self.dm_maxstroke_spinbox = QDoubleSpinBox(self.dm_groupbox)
        self.dm_maxstroke_spinbox.setObjectName(u"dm_maxstroke_spinbox")
        self.dm_maxstroke_spinbox.setKeyboardTracking(False)
        self.dm_maxstroke_spinbox.setDecimals(0)
        self.dm_maxstroke_spinbox.setMinimum(0.000000000000000)
        self.dm_maxstroke_spinbox.setMaximum(100.000000000000000)
        self.dm_maxstroke_spinbox.setSingleStep(5.000000000000000)

        self.formLayout_5.setWidget(0, QFormLayout.FieldRole, self.dm_maxstroke_spinbox)

        self.dm_strokemode_label = QLabel(self.dm_groupbox)
        self.dm_strokemode_label.setObjectName(u"dm_strokemode_label")

        self.formLayout_5.setWidget(1, QFormLayout.LabelRole, self.dm_strokemode_label)

        self.dm_strokemode_combobox = QComboBox(self.dm_groupbox)
        self.dm_strokemode_combobox.setObjectName(u"dm_strokemode_combobox")

        self.formLayout_5.setWidget(1, QFormLayout.FieldRole, self.dm_strokemode_combobox)

        self.dm_targetstroke_label = QLabel(self.dm_groupbox)
        self.dm_targetstroke_label.setObjectName(u"dm_targetstroke_label")

        self.formLayout_5.setWidget(2, QFormLayout.LabelRole, self.dm_targetstroke_label)

        self.dm_targetstroke_spinbox = QDoubleSpinBox(self.dm_groupbox)
        self.dm_targetstroke_spinbox.setObjectName(u"dm_targetstroke_spinbox")
        self.dm_targetstroke_spinbox.setKeyboardTracking(False)
        self.dm_targetstroke_spinbox.setDecimals(0)
        self.dm_targetstroke_spinbox.setMinimum(0.000000000000000)
        self.dm_targetstroke_spinbox.setMaximum(100.000000000000000)
        self.dm_targetstroke_spinbox.setSingleStep(5.000000000000000)

        self.formLayout_5.setWidget(2, QFormLayout.FieldRole, self.dm_targetstroke_spinbox)


        self.controls_layout.addWidget(self.dm_groupbox)

        self.observation_groupbox = QGroupBox(LoopControlsWidget)
        self.observation_groupbox.setObjectName(u"observation_groupbox")
        self.formLayout_6 = QFormLayout(self.observation_groupbox)
        self.formLayout_6.setObjectName(u"formLayout_6")
        self.formLayout_6.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.adc_synchronisation_label = QLabel(self.observation_groupbox)
        self.adc_synchronisation_label.setObjectName(u"adc_synchronisation_label")

        self.formLayout_6.setWidget(0, QFormLayout.LabelRole, self.adc_synchronisation_label)

        self.adc_synchronisation_checkbox = QCheckBox(self.observation_groupbox)
        self.adc_synchronisation_checkbox.setObjectName(u"adc_synchronisation_checkbox")

        self.formLayout_6.setWidget(0, QFormLayout.FieldRole, self.adc_synchronisation_checkbox)

        self.ttm_offloading_label = QLabel(self.observation_groupbox)
        self.ttm_offloading_label.setObjectName(u"ttm_offloading_label")

        self.formLayout_6.setWidget(1, QFormLayout.LabelRole, self.ttm_offloading_label)

        self.ttm_offloading_checkbox = QCheckBox(self.observation_groupbox)
        self.ttm_offloading_checkbox.setObjectName(u"ttm_offloading_checkbox")

        self.formLayout_6.setWidget(1, QFormLayout.FieldRole, self.ttm_offloading_checkbox)


        self.controls_layout.addWidget(self.observation_groupbox)


        self.horizontalLayout_2.addLayout(self.controls_layout)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.modalgains_groupbox = QGroupBox(LoopControlsWidget)
        self.modalgains_groupbox.setObjectName(u"modalgains_groupbox")
        self.gridLayout_11 = QGridLayout(self.modalgains_groupbox)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.modalgains_plot = KDraggableChartView(self.modalgains_groupbox)
        self.modalgains_plot.setObjectName(u"modalgains_plot")

        self.gridLayout_11.addWidget(self.modalgains_plot, 0, 0, 1, 1)

        self.modalgains_layout = QHBoxLayout()
        self.modalgains_layout.setObjectName(u"modalgains_layout")
        self.cutoff_label = QLabel(self.modalgains_groupbox)
        self.cutoff_label.setObjectName(u"cutoff_label")
        self.cutoff_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.modalgains_layout.addWidget(self.cutoff_label)

        self.cutoff_spinbox = QSpinBox(self.modalgains_groupbox)
        self.cutoff_spinbox.setObjectName(u"cutoff_spinbox")
        self.cutoff_spinbox.setKeyboardTracking(False)
        self.cutoff_spinbox.setMinimum(1)

        self.modalgains_layout.addWidget(self.cutoff_spinbox)

        self.last_label = QLabel(self.modalgains_groupbox)
        self.last_label.setObjectName(u"last_label")
        self.last_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.modalgains_layout.addWidget(self.last_label)

        self.last_spinbox = QSpinBox(self.modalgains_groupbox)
        self.last_spinbox.setObjectName(u"last_spinbox")
        self.last_spinbox.setKeyboardTracking(False)
        self.last_spinbox.setMinimum(1)

        self.modalgains_layout.addWidget(self.last_spinbox)

        self.law_label = QLabel(self.modalgains_groupbox)
        self.law_label.setObjectName(u"law_label")
        self.law_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.modalgains_layout.addWidget(self.law_label)

        self.law_combobox = QComboBox(self.modalgains_groupbox)
        self.law_combobox.setObjectName(u"law_combobox")

        self.modalgains_layout.addWidget(self.law_combobox)


        self.gridLayout_11.addLayout(self.modalgains_layout, 3, 0, 1, 1)


        self.gridLayout.addWidget(self.modalgains_groupbox, 0, 0, 1, 1)

        self.modes_groupbox = QGroupBox(LoopControlsWidget)
        self.modes_groupbox.setObjectName(u"modes_groupbox")
        self.gridLayout_2 = QGridLayout(self.modes_groupbox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.modes_plot = KChartView(self.modes_groupbox)
        self.modes_plot.setObjectName(u"modes_plot")

        self.gridLayout_2.addWidget(self.modes_plot, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.modes_groupbox, 1, 0, 1, 1)


        self.horizontalLayout_2.addLayout(self.gridLayout)


        self.retranslateUi(LoopControlsWidget)

        QMetaObject.connectSlotsByName(LoopControlsWidget)
    # setupUi

    def retranslateUi(self, LoopControlsWidget):
        LoopControlsWidget.setWindowTitle(QCoreApplication.translate("LoopControlsWidget", u"Loop Controls - KalAO", None))
        self.dmloop_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Deformable Mirror Loop", None))
        self.dmloop_on_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop ON", None))
        self.dmloop_on_checkbox.setText("")
        self.dmloopgain_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Gain", None))
        self.dmloop_mult_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Mult", None))
        self.dmloop_limit_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Limit", None))
        self.dmloop_zero_button.setText(QCoreApplication.translate("LoopControlsWidget", u"Zero loop", None))
        self.ttmloop_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Tip-Tilt Mirror Loop", None))
        self.ttmloop_on_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop ON", None))
        self.ttmloop_gain_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Gain", None))
        self.ttmloop_mult_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Mult", None))
        self.ttmloop_limit_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Loop Limit", None))
        self.ttmloop_on_checkbox.setText("")
        self.ttmloop_zero_button.setText(QCoreApplication.translate("LoopControlsWidget", u"Zero loop", None))
        self.wfs_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Wavefront Sensor (N\u00fcv\u00fc)", None))
        self.wfs_emgain_label.setText(QCoreApplication.translate("LoopControlsWidget", u"EM Gain", None))
        self.wfs_exposuretime_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Exposure time", None))
        self.wfs_exposuretime_spinbox.setSuffix(QCoreApplication.translate("LoopControlsWidget", u" ms", None))
        self.wfs_autogain_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Auto-gain", None))
        self.wfs_autogain_checkbox.setText("")
        self.wfs_autogain_setting_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Auto-gain setting", None))
        self.wfs_algorithm_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Algorithm", None))
        self.dm_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Deformable Mirror (Boston Micromachines Corporation)", None))
        self.dm_maxstroke_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Max stroke", None))
        self.dm_maxstroke_spinbox.setSuffix(QCoreApplication.translate("LoopControlsWidget", u" %", None))
        self.dm_strokemode_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Stroke mode", None))
        self.dm_targetstroke_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Target stroke", None))
        self.dm_targetstroke_spinbox.setSuffix(QCoreApplication.translate("LoopControlsWidget", u" %", None))
        self.observation_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Observation", None))
        self.adc_synchronisation_label.setText(QCoreApplication.translate("LoopControlsWidget", u"ADC Synchronisation", None))
        self.adc_synchronisation_checkbox.setText("")
        self.ttm_offloading_label.setText(QCoreApplication.translate("LoopControlsWidget", u"TTM to Telescope Offloading", None))
        self.ttm_offloading_checkbox.setText("")
        self.modalgains_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Modal Gains", None))
        self.cutoff_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Cut-off", None))
        self.last_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Last mode", None))
        self.law_label.setText(QCoreApplication.translate("LoopControlsWidget", u"Law", None))
        self.modes_groupbox.setTitle(QCoreApplication.translate("LoopControlsWidget", u"Mode Coefficients", None))
    # retranslateUi

