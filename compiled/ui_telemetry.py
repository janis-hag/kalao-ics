# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'telemetry.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QWidget)

from kalao.guis.utils.widgets import KDraggableChartView

class Ui_TelemetryWidget(object):
    def setupUi(self, TelemetryWidget):
        if not TelemetryWidget.objectName():
            TelemetryWidget.setObjectName(u"TelemetryWidget")
        TelemetryWidget.resize(1265, 934)
        self.gridLayout = QGridLayout(TelemetryWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.flux_groupbox = QGroupBox(TelemetryWidget)
        self.flux_groupbox.setObjectName(u"flux_groupbox")
        self.gridLayout_6 = QGridLayout(self.flux_groupbox)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.flux_std_label = QLabel(self.flux_groupbox)
        self.flux_std_label.setObjectName(u"flux_std_label")
        self.flux_std_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_6.addWidget(self.flux_std_label, 1, 4, 1, 1)

        self.flux_avg_label = QLabel(self.flux_groupbox)
        self.flux_avg_label.setObjectName(u"flux_avg_label")

        self.gridLayout_6.addWidget(self.flux_avg_label, 2, 0, 1, 1)

        self.flux_avg_std_checkbox = QCheckBox(self.flux_groupbox)
        self.flux_avg_std_checkbox.setObjectName(u"flux_avg_std_checkbox")

        self.gridLayout_6.addWidget(self.flux_avg_std_checkbox, 2, 3, 1, 1)

        self.flux_max_std_checkbox = QCheckBox(self.flux_groupbox)
        self.flux_max_std_checkbox.setObjectName(u"flux_max_std_checkbox")

        self.gridLayout_6.addWidget(self.flux_max_std_checkbox, 3, 3, 1, 1)

        self.flux_avg_std_spinbox = QDoubleSpinBox(self.flux_groupbox)
        self.flux_avg_std_spinbox.setObjectName(u"flux_avg_std_spinbox")
        self.flux_avg_std_spinbox.setReadOnly(True)
        self.flux_avg_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.flux_avg_std_spinbox.setDecimals(0)
        self.flux_avg_std_spinbox.setMaximum(1000000.000000000000000)

        self.gridLayout_6.addWidget(self.flux_avg_std_spinbox, 2, 4, 1, 1)

        self.flux_plot = KDraggableChartView(self.flux_groupbox)
        self.flux_plot.setObjectName(u"flux_plot")

        self.gridLayout_6.addWidget(self.flux_plot, 0, 0, 1, 5)

        self.flux_avg_mean_checkbox = QCheckBox(self.flux_groupbox)
        self.flux_avg_mean_checkbox.setObjectName(u"flux_avg_mean_checkbox")
        self.flux_avg_mean_checkbox.setChecked(True)

        self.gridLayout_6.addWidget(self.flux_avg_mean_checkbox, 2, 1, 1, 1)

        self.flux_max_label = QLabel(self.flux_groupbox)
        self.flux_max_label.setObjectName(u"flux_max_label")

        self.gridLayout_6.addWidget(self.flux_max_label, 3, 0, 1, 1)

        self.flux_avg_mean_spinbox = QDoubleSpinBox(self.flux_groupbox)
        self.flux_avg_mean_spinbox.setObjectName(u"flux_avg_mean_spinbox")
        self.flux_avg_mean_spinbox.setReadOnly(True)
        self.flux_avg_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.flux_avg_mean_spinbox.setDecimals(0)
        self.flux_avg_mean_spinbox.setMinimum(-1000000.000000000000000)
        self.flux_avg_mean_spinbox.setMaximum(1000000.000000000000000)

        self.gridLayout_6.addWidget(self.flux_avg_mean_spinbox, 2, 2, 1, 1)

        self.flux_max_std_spinbox = QDoubleSpinBox(self.flux_groupbox)
        self.flux_max_std_spinbox.setObjectName(u"flux_max_std_spinbox")
        self.flux_max_std_spinbox.setReadOnly(True)
        self.flux_max_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.flux_max_std_spinbox.setDecimals(0)
        self.flux_max_std_spinbox.setMaximum(1000000.000000000000000)

        self.gridLayout_6.addWidget(self.flux_max_std_spinbox, 3, 4, 1, 1)

        self.flux_max_mean_spinbox = QDoubleSpinBox(self.flux_groupbox)
        self.flux_max_mean_spinbox.setObjectName(u"flux_max_mean_spinbox")
        self.flux_max_mean_spinbox.setReadOnly(True)
        self.flux_max_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.flux_max_mean_spinbox.setDecimals(0)
        self.flux_max_mean_spinbox.setMinimum(-1000000.000000000000000)
        self.flux_max_mean_spinbox.setMaximum(1000000.000000000000000)

        self.gridLayout_6.addWidget(self.flux_max_mean_spinbox, 3, 2, 1, 1)

        self.flux_max_mean_checkbox = QCheckBox(self.flux_groupbox)
        self.flux_max_mean_checkbox.setObjectName(u"flux_max_mean_checkbox")
        self.flux_max_mean_checkbox.setChecked(True)

        self.gridLayout_6.addWidget(self.flux_max_mean_checkbox, 3, 1, 1, 1)

        self.flux_mean_label = QLabel(self.flux_groupbox)
        self.flux_mean_label.setObjectName(u"flux_mean_label")
        self.flux_mean_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_6.addWidget(self.flux_mean_label, 1, 2, 1, 1)

        self.gridLayout_6.setColumnStretch(2, 1)
        self.gridLayout_6.setColumnStretch(4, 1)

        self.gridLayout.addWidget(self.flux_groupbox, 0, 1, 1, 1)

        self.ttm_groupbox = QGroupBox(TelemetryWidget)
        self.ttm_groupbox.setObjectName(u"ttm_groupbox")
        self.gridLayout_4 = QGridLayout(self.ttm_groupbox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.ttm_std_label = QLabel(self.ttm_groupbox)
        self.ttm_std_label.setObjectName(u"ttm_std_label")
        self.ttm_std_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_4.addWidget(self.ttm_std_label, 1, 4, 1, 1)

        self.tip_label = QLabel(self.ttm_groupbox)
        self.tip_label.setObjectName(u"tip_label")

        self.gridLayout_4.addWidget(self.tip_label, 2, 0, 1, 1)

        self.tip_std_checkbox = QCheckBox(self.ttm_groupbox)
        self.tip_std_checkbox.setObjectName(u"tip_std_checkbox")

        self.gridLayout_4.addWidget(self.tip_std_checkbox, 2, 3, 1, 1)

        self.tilt_std_checkbox = QCheckBox(self.ttm_groupbox)
        self.tilt_std_checkbox.setObjectName(u"tilt_std_checkbox")

        self.gridLayout_4.addWidget(self.tilt_std_checkbox, 3, 3, 1, 1)

        self.tip_std_spinbox = QDoubleSpinBox(self.ttm_groupbox)
        self.tip_std_spinbox.setObjectName(u"tip_std_spinbox")
        self.tip_std_spinbox.setReadOnly(True)
        self.tip_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tip_std_spinbox.setMaximum(99.000000000000000)

        self.gridLayout_4.addWidget(self.tip_std_spinbox, 2, 4, 1, 1)

        self.ttm_plot = KDraggableChartView(self.ttm_groupbox)
        self.ttm_plot.setObjectName(u"ttm_plot")

        self.gridLayout_4.addWidget(self.ttm_plot, 0, 0, 1, 5)

        self.tip_mean_checkbox = QCheckBox(self.ttm_groupbox)
        self.tip_mean_checkbox.setObjectName(u"tip_mean_checkbox")
        self.tip_mean_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.tip_mean_checkbox, 2, 1, 1, 1)

        self.tilt_label = QLabel(self.ttm_groupbox)
        self.tilt_label.setObjectName(u"tilt_label")

        self.gridLayout_4.addWidget(self.tilt_label, 3, 0, 1, 1)

        self.tip_mean_spinbox = QDoubleSpinBox(self.ttm_groupbox)
        self.tip_mean_spinbox.setObjectName(u"tip_mean_spinbox")
        self.tip_mean_spinbox.setReadOnly(True)
        self.tip_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tip_mean_spinbox.setMinimum(-99.000000000000000)
        self.tip_mean_spinbox.setMaximum(99.000000000000000)

        self.gridLayout_4.addWidget(self.tip_mean_spinbox, 2, 2, 1, 1)

        self.tilt_std_spinbox = QDoubleSpinBox(self.ttm_groupbox)
        self.tilt_std_spinbox.setObjectName(u"tilt_std_spinbox")
        self.tilt_std_spinbox.setReadOnly(True)
        self.tilt_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tilt_std_spinbox.setMaximum(99.000000000000000)

        self.gridLayout_4.addWidget(self.tilt_std_spinbox, 3, 4, 1, 1)

        self.tilt_mean_spinbox = QDoubleSpinBox(self.ttm_groupbox)
        self.tilt_mean_spinbox.setObjectName(u"tilt_mean_spinbox")
        self.tilt_mean_spinbox.setReadOnly(True)
        self.tilt_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.tilt_mean_spinbox.setMinimum(-99.000000000000000)
        self.tilt_mean_spinbox.setMaximum(99.000000000000000)

        self.gridLayout_4.addWidget(self.tilt_mean_spinbox, 3, 2, 1, 1)

        self.tilt_mean_checkbox = QCheckBox(self.ttm_groupbox)
        self.tilt_mean_checkbox.setObjectName(u"tilt_mean_checkbox")
        self.tilt_mean_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.tilt_mean_checkbox, 3, 1, 1, 1)

        self.ttm_mean_label = QLabel(self.ttm_groupbox)
        self.ttm_mean_label.setObjectName(u"ttm_mean_label")
        self.ttm_mean_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_4.addWidget(self.ttm_mean_label, 1, 2, 1, 1)

        self.gridLayout_4.setColumnStretch(2, 1)
        self.gridLayout_4.setColumnStretch(4, 1)

        self.gridLayout.addWidget(self.ttm_groupbox, 0, 0, 1, 1)

        self.tiptilt_spectrum_groupbox = QGroupBox(TelemetryWidget)
        self.tiptilt_spectrum_groupbox.setObjectName(u"tiptilt_spectrum_groupbox")
        self.gridLayout_3 = QGridLayout(self.tiptilt_spectrum_groupbox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.tiptilt_spectrum_plot = KDraggableChartView(self.tiptilt_spectrum_groupbox)
        self.tiptilt_spectrum_plot.setObjectName(u"tiptilt_spectrum_plot")

        self.gridLayout_3.addWidget(self.tiptilt_spectrum_plot, 0, 0, 1, 1)

        self.tiptilt_spectrum_layout = QHBoxLayout()
        self.tiptilt_spectrum_layout.setObjectName(u"tiptilt_spectrum_layout")
        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tiptilt_spectrum_layout.addItem(self.horizontalSpacer)

        self.tip_spectrum_checkbox = QCheckBox(self.tiptilt_spectrum_groupbox)
        self.tip_spectrum_checkbox.setObjectName(u"tip_spectrum_checkbox")
        self.tip_spectrum_checkbox.setChecked(True)

        self.tiptilt_spectrum_layout.addWidget(self.tip_spectrum_checkbox)

        self.tilt_spectrum_checkbox = QCheckBox(self.tiptilt_spectrum_groupbox)
        self.tilt_spectrum_checkbox.setObjectName(u"tilt_spectrum_checkbox")
        self.tilt_spectrum_checkbox.setChecked(True)

        self.tiptilt_spectrum_layout.addWidget(self.tilt_spectrum_checkbox)

        self.horizontalSpacer_2 = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tiptilt_spectrum_layout.addItem(self.horizontalSpacer_2)


        self.gridLayout_3.addLayout(self.tiptilt_spectrum_layout, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.tiptilt_spectrum_groupbox, 1, 0, 1, 1)

        self.settings_groupbox = QGroupBox(TelemetryWidget)
        self.settings_groupbox.setObjectName(u"settings_groupbox")
        self.gridLayout_2 = QGridLayout(self.settings_groupbox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.binning_label = QLabel(self.settings_groupbox)
        self.binning_label.setObjectName(u"binning_label")
        self.binning_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.binning_label, 0, 0, 1, 1)

        self.binning_spinbox = QDoubleSpinBox(self.settings_groupbox)
        self.binning_spinbox.setObjectName(u"binning_spinbox")
        self.binning_spinbox.setKeyboardTracking(False)
        self.binning_spinbox.setDecimals(2)
        self.binning_spinbox.setMinimum(0.010000000000000)
        self.binning_spinbox.setMaximum(99.000000000000000)
        self.binning_spinbox.setSingleStep(0.100000000000000)
        self.binning_spinbox.setValue(0.100000000000000)

        self.gridLayout_2.addWidget(self.binning_spinbox, 0, 1, 1, 1)

        self.length_label = QLabel(self.settings_groupbox)
        self.length_label.setObjectName(u"length_label")
        self.length_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.length_label, 1, 0, 1, 1)

        self.length_spinbox = QDoubleSpinBox(self.settings_groupbox)
        self.length_spinbox.setObjectName(u"length_spinbox")
        self.length_spinbox.setKeyboardTracking(False)
        self.length_spinbox.setDecimals(0)
        self.length_spinbox.setMinimum(1.000000000000000)
        self.length_spinbox.setMaximum(3600.000000000000000)
        self.length_spinbox.setSingleStep(30.000000000000000)
        self.length_spinbox.setValue(60.000000000000000)

        self.gridLayout_2.addWidget(self.length_spinbox, 1, 1, 1, 1)

        self.gridLayout_2.setColumnStretch(1, 1)

        self.gridLayout.addWidget(self.settings_groupbox, 2, 0, 1, 1)

        self.slopes_groupbox = QGroupBox(TelemetryWidget)
        self.slopes_groupbox.setObjectName(u"slopes_groupbox")
        self.gridLayout_5 = QGridLayout(self.slopes_groupbox)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.slope_y_avg_label = QLabel(self.slopes_groupbox)
        self.slope_y_avg_label.setObjectName(u"slope_y_avg_label")

        self.gridLayout_5.addWidget(self.slope_y_avg_label, 3, 0, 1, 1)

        self.slope_y_avg_mean_checkbox = QCheckBox(self.slopes_groupbox)
        self.slope_y_avg_mean_checkbox.setObjectName(u"slope_y_avg_mean_checkbox")
        self.slope_y_avg_mean_checkbox.setChecked(True)

        self.gridLayout_5.addWidget(self.slope_y_avg_mean_checkbox, 3, 1, 1, 1)

        self.slope_y_avg_std_checkbox = QCheckBox(self.slopes_groupbox)
        self.slope_y_avg_std_checkbox.setObjectName(u"slope_y_avg_std_checkbox")

        self.gridLayout_5.addWidget(self.slope_y_avg_std_checkbox, 3, 3, 1, 1)

        self.slope_y_avg_std_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.slope_y_avg_std_spinbox.setObjectName(u"slope_y_avg_std_spinbox")
        self.slope_y_avg_std_spinbox.setReadOnly(True)
        self.slope_y_avg_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.slope_y_avg_std_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.slope_y_avg_std_spinbox, 3, 4, 1, 1)

        self.slopes_mean_label = QLabel(self.slopes_groupbox)
        self.slopes_mean_label.setObjectName(u"slopes_mean_label")
        self.slopes_mean_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.slopes_mean_label, 1, 2, 1, 1)

        self.slope_y_avg_mean_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.slope_y_avg_mean_spinbox.setObjectName(u"slope_y_avg_mean_spinbox")
        self.slope_y_avg_mean_spinbox.setReadOnly(True)
        self.slope_y_avg_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.slope_y_avg_mean_spinbox.setMinimum(-999.000000000000000)
        self.slope_y_avg_mean_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.slope_y_avg_mean_spinbox, 3, 2, 1, 1)

        self.slopes_std_label = QLabel(self.slopes_groupbox)
        self.slopes_std_label.setObjectName(u"slopes_std_label")
        self.slopes_std_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.slopes_std_label, 1, 4, 1, 1)

        self.slope_x_avg_label = QLabel(self.slopes_groupbox)
        self.slope_x_avg_label.setObjectName(u"slope_x_avg_label")

        self.gridLayout_5.addWidget(self.slope_x_avg_label, 2, 0, 1, 1)

        self.slope_x_avg_std_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.slope_x_avg_std_spinbox.setObjectName(u"slope_x_avg_std_spinbox")
        self.slope_x_avg_std_spinbox.setReadOnly(True)
        self.slope_x_avg_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.slope_x_avg_std_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.slope_x_avg_std_spinbox, 2, 4, 1, 1)

        self.slope_x_avg_std_checkbox = QCheckBox(self.slopes_groupbox)
        self.slope_x_avg_std_checkbox.setObjectName(u"slope_x_avg_std_checkbox")

        self.gridLayout_5.addWidget(self.slope_x_avg_std_checkbox, 2, 3, 1, 1)

        self.slopes_plot = KDraggableChartView(self.slopes_groupbox)
        self.slopes_plot.setObjectName(u"slopes_plot")

        self.gridLayout_5.addWidget(self.slopes_plot, 0, 0, 1, 5)

        self.slope_x_avg_mean_checkbox = QCheckBox(self.slopes_groupbox)
        self.slope_x_avg_mean_checkbox.setObjectName(u"slope_x_avg_mean_checkbox")
        self.slope_x_avg_mean_checkbox.setChecked(True)

        self.gridLayout_5.addWidget(self.slope_x_avg_mean_checkbox, 2, 1, 1, 1)

        self.slope_x_avg_mean_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.slope_x_avg_mean_spinbox.setObjectName(u"slope_x_avg_mean_spinbox")
        self.slope_x_avg_mean_spinbox.setReadOnly(True)
        self.slope_x_avg_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.slope_x_avg_mean_spinbox.setMinimum(-999.000000000000000)
        self.slope_x_avg_mean_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.slope_x_avg_mean_spinbox, 2, 2, 1, 1)

        self.residual_rms_label = QLabel(self.slopes_groupbox)
        self.residual_rms_label.setObjectName(u"residual_rms_label")

        self.gridLayout_5.addWidget(self.residual_rms_label, 4, 0, 1, 1)

        self.residual_rms_mean_checkbox = QCheckBox(self.slopes_groupbox)
        self.residual_rms_mean_checkbox.setObjectName(u"residual_rms_mean_checkbox")
        self.residual_rms_mean_checkbox.setChecked(True)

        self.gridLayout_5.addWidget(self.residual_rms_mean_checkbox, 4, 1, 1, 1)

        self.residual_rms_std_checkbox = QCheckBox(self.slopes_groupbox)
        self.residual_rms_std_checkbox.setObjectName(u"residual_rms_std_checkbox")

        self.gridLayout_5.addWidget(self.residual_rms_std_checkbox, 4, 3, 1, 1)

        self.residual_rms_mean_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.residual_rms_mean_spinbox.setObjectName(u"residual_rms_mean_spinbox")
        self.residual_rms_mean_spinbox.setReadOnly(True)
        self.residual_rms_mean_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.residual_rms_mean_spinbox.setMinimum(-999.000000000000000)
        self.residual_rms_mean_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.residual_rms_mean_spinbox, 4, 2, 1, 1)

        self.residual_rms_std_spinbox = QDoubleSpinBox(self.slopes_groupbox)
        self.residual_rms_std_spinbox.setObjectName(u"residual_rms_std_spinbox")
        self.residual_rms_std_spinbox.setReadOnly(True)
        self.residual_rms_std_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.residual_rms_std_spinbox.setMaximum(999.000000000000000)

        self.gridLayout_5.addWidget(self.residual_rms_std_spinbox, 4, 4, 1, 1)

        self.gridLayout_5.setColumnStretch(2, 1)
        self.gridLayout_5.setColumnStretch(4, 1)

        self.gridLayout.addWidget(self.slopes_groupbox, 1, 1, 2, 1)


        self.retranslateUi(TelemetryWidget)

        QMetaObject.connectSlotsByName(TelemetryWidget)
    # setupUi

    def retranslateUi(self, TelemetryWidget):
        TelemetryWidget.setWindowTitle(QCoreApplication.translate("TelemetryWidget", u"Telemetry - KalAO", None))
        self.flux_groupbox.setTitle(QCoreApplication.translate("TelemetryWidget", u"Flux", None))
        self.flux_std_label.setText(QCoreApplication.translate("TelemetryWidget", u"RMS", None))
        self.flux_avg_label.setText(QCoreApplication.translate("TelemetryWidget", u"Flux avg.", None))
        self.flux_avg_std_checkbox.setText("")
        self.flux_max_std_checkbox.setText("")
        self.flux_avg_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" ADU", None))
        self.flux_avg_mean_checkbox.setText("")
        self.flux_max_label.setText(QCoreApplication.translate("TelemetryWidget", u"Flux max.", None))
        self.flux_avg_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" ADU", None))
        self.flux_max_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" ADU", None))
        self.flux_max_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" ADU", None))
        self.flux_max_mean_checkbox.setText("")
        self.flux_mean_label.setText(QCoreApplication.translate("TelemetryWidget", u"Average", None))
        self.ttm_groupbox.setTitle(QCoreApplication.translate("TelemetryWidget", u"Tip-Tilt", None))
        self.ttm_std_label.setText(QCoreApplication.translate("TelemetryWidget", u"RMS", None))
        self.tip_label.setText(QCoreApplication.translate("TelemetryWidget", u"Tip", None))
        self.tip_std_checkbox.setText("")
        self.tilt_std_checkbox.setText("")
        self.tip_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.tip_mean_checkbox.setText("")
        self.tilt_label.setText(QCoreApplication.translate("TelemetryWidget", u"Tilt", None))
        self.tip_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.tilt_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.tilt_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.tilt_mean_checkbox.setText("")
        self.ttm_mean_label.setText(QCoreApplication.translate("TelemetryWidget", u"Average", None))
        self.tiptilt_spectrum_groupbox.setTitle(QCoreApplication.translate("TelemetryWidget", u"Tip-Tilt Spectrum", None))
        self.tip_spectrum_checkbox.setText(QCoreApplication.translate("TelemetryWidget", u"Tip spectrum", None))
        self.tilt_spectrum_checkbox.setText(QCoreApplication.translate("TelemetryWidget", u"Tilt spectrum", None))
        self.settings_groupbox.setTitle(QCoreApplication.translate("TelemetryWidget", u"Settings", None))
        self.binning_label.setText(QCoreApplication.translate("TelemetryWidget", u"Temporal binning", None))
        self.binning_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" s", None))
        self.length_label.setText(QCoreApplication.translate("TelemetryWidget", u"Plots duration", None))
        self.length_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u" s", None))
        self.slopes_groupbox.setTitle(QCoreApplication.translate("TelemetryWidget", u"Slopes", None))
        self.slope_y_avg_label.setText(QCoreApplication.translate("TelemetryWidget", u"Slope Y", None))
        self.slope_y_avg_mean_checkbox.setText("")
        self.slope_y_avg_std_checkbox.setText("")
        self.slope_y_avg_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.slopes_mean_label.setText(QCoreApplication.translate("TelemetryWidget", u"Average", None))
        self.slope_y_avg_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.slopes_std_label.setText(QCoreApplication.translate("TelemetryWidget", u"RMS", None))
        self.slope_x_avg_label.setText(QCoreApplication.translate("TelemetryWidget", u"Slope X", None))
        self.slope_x_avg_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.slope_x_avg_std_checkbox.setText("")
        self.slope_x_avg_mean_checkbox.setText("")
        self.slope_x_avg_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.residual_rms_label.setText(QCoreApplication.translate("TelemetryWidget", u"Residual", None))
        self.residual_rms_mean_checkbox.setText("")
        self.residual_rms_std_checkbox.setText("")
        self.residual_rms_mean_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
        self.residual_rms_std_spinbox.setSuffix(QCoreApplication.translate("TelemetryWidget", u"\"", None))
    # retranslateUi

