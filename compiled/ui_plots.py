# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plots.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDateTimeEdit, QDoubleSpinBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QToolButton, QTreeWidget,
    QTreeWidgetItem, QWidget)

from kalao.guis.utils.widgets import (KChartView, KDateTimeEdit)
from . import rc_assets

class Ui_PlotsWidget(object):
    def setupUi(self, PlotsWidget):
        if not PlotsWidget.objectName():
            PlotsWidget.setObjectName(u"PlotsWidget")
        PlotsWidget.resize(1434, 687)
        self.gridLayout = QGridLayout(PlotsWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scale_layout = QHBoxLayout()
        self.scale_layout.setObjectName(u"scale_layout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer)

        self.min_label = QLabel(PlotsWidget)
        self.min_label.setObjectName(u"min_label")

        self.scale_layout.addWidget(self.min_label)

        self.min_spinbox = QDoubleSpinBox(PlotsWidget)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setDecimals(1)
        self.min_spinbox.setMinimum(-999.000000000000000)
        self.min_spinbox.setMaximum(999.000000000000000)

        self.scale_layout.addWidget(self.min_spinbox)

        self.horizontalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer_3)

        self.max_label = QLabel(PlotsWidget)
        self.max_label.setObjectName(u"max_label")

        self.scale_layout.addWidget(self.max_label)

        self.max_spinbox = QDoubleSpinBox(PlotsWidget)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setDecimals(1)
        self.max_spinbox.setMinimum(-999.000000000000000)
        self.max_spinbox.setMaximum(999.000000000000000)

        self.scale_layout.addWidget(self.max_spinbox)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.scale_layout, 0, 0, 1, 1)

        self.plots_view = KChartView(PlotsWidget)
        self.plots_view.setObjectName(u"plots_view")

        self.gridLayout.addWidget(self.plots_view, 1, 0, 1, 1)

        self.side_layout = QFormLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.side_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.since_label = QLabel(PlotsWidget)
        self.since_label.setObjectName(u"since_label")

        self.side_layout.setWidget(0, QFormLayout.LabelRole, self.since_label)

        self.since_datetimeedit = KDateTimeEdit(PlotsWidget)
        self.since_datetimeedit.setObjectName(u"since_datetimeedit")
        self.since_datetimeedit.setCurrentSection(QDateTimeEdit.Section.HourSection)

        self.side_layout.setWidget(0, QFormLayout.FieldRole, self.since_datetimeedit)

        self.until_label = QLabel(PlotsWidget)
        self.until_label.setObjectName(u"until_label")

        self.side_layout.setWidget(1, QFormLayout.LabelRole, self.until_label)

        self.until_datetimeedit = KDateTimeEdit(PlotsWidget)
        self.until_datetimeedit.setObjectName(u"until_datetimeedit")
        self.until_datetimeedit.setCurrentSection(QDateTimeEdit.Section.HourSection)

        self.side_layout.setWidget(1, QFormLayout.FieldRole, self.until_datetimeedit)

        self.last_label = QLabel(PlotsWidget)
        self.last_label.setObjectName(u"last_label")

        self.side_layout.setWidget(2, QFormLayout.LabelRole, self.last_label)

        self.last_layout = QHBoxLayout()
        self.last_layout.setObjectName(u"last_layout")
        self.last_5minutes_button = QToolButton(PlotsWidget)
        self.last_5minutes_button.setObjectName(u"last_5minutes_button")

        self.last_layout.addWidget(self.last_5minutes_button)

        self.last_hour_button = QToolButton(PlotsWidget)
        self.last_hour_button.setObjectName(u"last_hour_button")

        self.last_layout.addWidget(self.last_hour_button)

        self.last_day_button = QToolButton(PlotsWidget)
        self.last_day_button.setObjectName(u"last_day_button")

        self.last_layout.addWidget(self.last_day_button)

        self.last_week_button = QToolButton(PlotsWidget)
        self.last_week_button.setObjectName(u"last_week_button")

        self.last_layout.addWidget(self.last_week_button)

        self.last_month_button = QToolButton(PlotsWidget)
        self.last_month_button.setObjectName(u"last_month_button")

        self.last_layout.addWidget(self.last_month_button)


        self.side_layout.setLayout(2, QFormLayout.FieldRole, self.last_layout)

        self.tonight_button = QPushButton(PlotsWidget)
        self.tonight_button.setObjectName(u"tonight_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/clock.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tonight_button.setIcon(icon)

        self.side_layout.setWidget(3, QFormLayout.SpanningRole, self.tonight_button)

        self.monitoring_treeview = QTreeWidget(PlotsWidget)
        self.monitoring_treeview.setObjectName(u"monitoring_treeview")
        self.monitoring_treeview.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))
        self.monitoring_treeview.setMouseTracking(True)

        self.side_layout.setWidget(4, QFormLayout.SpanningRole, self.monitoring_treeview)

        self.obs_treeview = QTreeWidget(PlotsWidget)
        self.obs_treeview.setObjectName(u"obs_treeview")
        self.obs_treeview.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))
        self.obs_treeview.setMouseTracking(True)

        self.side_layout.setWidget(5, QFormLayout.SpanningRole, self.obs_treeview)

        self.autoupdate_groupbox = QGroupBox(PlotsWidget)
        self.autoupdate_groupbox.setObjectName(u"autoupdate_groupbox")
        self.formLayout = QFormLayout(self.autoupdate_groupbox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.autoupdate_checkbox = QCheckBox(self.autoupdate_groupbox)
        self.autoupdate_checkbox.setObjectName(u"autoupdate_checkbox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.autoupdate_checkbox)

        self.autoupdate_label = QLabel(self.autoupdate_groupbox)
        self.autoupdate_label.setObjectName(u"autoupdate_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.autoupdate_label)

        self.autoupdate_refresh_rate_spinbox = QDoubleSpinBox(self.autoupdate_groupbox)
        self.autoupdate_refresh_rate_spinbox.setObjectName(u"autoupdate_refresh_rate_spinbox")
        self.autoupdate_refresh_rate_spinbox.setKeyboardTracking(False)
        self.autoupdate_refresh_rate_spinbox.setDecimals(1)
        self.autoupdate_refresh_rate_spinbox.setMinimum(0.100000000000000)
        self.autoupdate_refresh_rate_spinbox.setMaximum(3600.000000000000000)
        self.autoupdate_refresh_rate_spinbox.setValue(1.000000000000000)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.autoupdate_refresh_rate_spinbox)

        self.autoupdate_database_button = QRadioButton(self.autoupdate_groupbox)
        self.autoupdate_database_button.setObjectName(u"autoupdate_database_button")
        self.autoupdate_database_button.setChecked(True)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.autoupdate_database_button)

        self.autoupdate_direct_button = QRadioButton(self.autoupdate_groupbox)
        self.autoupdate_direct_button.setObjectName(u"autoupdate_direct_button")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.autoupdate_direct_button)

        self.autoupdate_database_label = QLabel(self.autoupdate_groupbox)
        self.autoupdate_database_label.setObjectName(u"autoupdate_database_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.autoupdate_database_label)

        self.autoupdate_refresh_rate_label = QLabel(self.autoupdate_groupbox)
        self.autoupdate_refresh_rate_label.setObjectName(u"autoupdate_refresh_rate_label")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.autoupdate_refresh_rate_label)

        self.autoupdate_direct_label = QLabel(self.autoupdate_groupbox)
        self.autoupdate_direct_label.setObjectName(u"autoupdate_direct_label")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.autoupdate_direct_label)


        self.side_layout.setWidget(6, QFormLayout.SpanningRole, self.autoupdate_groupbox)

        self.clear_all_button = QPushButton(PlotsWidget)
        self.clear_all_button.setObjectName(u"clear_all_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/edit-clear-all.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.clear_all_button.setIcon(icon1)

        self.side_layout.setWidget(7, QFormLayout.SpanningRole, self.clear_all_button)

        self.plot_button = QPushButton(PlotsWidget)
        self.plot_button.setObjectName(u"plot_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/view-media-chart.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.plot_button.setIcon(icon2)

        self.side_layout.setWidget(8, QFormLayout.SpanningRole, self.plot_button)


        self.gridLayout.addLayout(self.side_layout, 0, 1, 3, 1)

        self.gridLayout.setColumnStretch(0, 1)

        self.retranslateUi(PlotsWidget)

        QMetaObject.connectSlotsByName(PlotsWidget)
    # setupUi

    def retranslateUi(self, PlotsWidget):
        PlotsWidget.setWindowTitle(QCoreApplication.translate("PlotsWidget", u"Plots - KalAO", None))
        self.min_label.setText(QCoreApplication.translate("PlotsWidget", u"Min", None))
        self.max_label.setText(QCoreApplication.translate("PlotsWidget", u"Max", None))
        self.since_label.setText(QCoreApplication.translate("PlotsWidget", u"Since", None))
        self.since_datetimeedit.setDisplayFormat(QCoreApplication.translate("PlotsWidget", u"HH:mm:ss dd.MM.yy", None))
        self.until_label.setText(QCoreApplication.translate("PlotsWidget", u"Until", None))
        self.until_datetimeedit.setDisplayFormat(QCoreApplication.translate("PlotsWidget", u"HH:mm:ss dd.MM.yy", None))
        self.last_label.setText(QCoreApplication.translate("PlotsWidget", u"Last", None))
#if QT_CONFIG(tooltip)
        self.last_5minutes_button.setToolTip(QCoreApplication.translate("PlotsWidget", u"One hour", None))
#endif // QT_CONFIG(tooltip)
        self.last_5minutes_button.setText(QCoreApplication.translate("PlotsWidget", u"5m", None))
#if QT_CONFIG(tooltip)
        self.last_hour_button.setToolTip(QCoreApplication.translate("PlotsWidget", u"One hour", None))
#endif // QT_CONFIG(tooltip)
        self.last_hour_button.setText(QCoreApplication.translate("PlotsWidget", u"1h", None))
#if QT_CONFIG(tooltip)
        self.last_day_button.setToolTip(QCoreApplication.translate("PlotsWidget", u"One day", None))
#endif // QT_CONFIG(tooltip)
        self.last_day_button.setText(QCoreApplication.translate("PlotsWidget", u"1d", None))
#if QT_CONFIG(tooltip)
        self.last_week_button.setToolTip(QCoreApplication.translate("PlotsWidget", u"One week", None))
#endif // QT_CONFIG(tooltip)
        self.last_week_button.setText(QCoreApplication.translate("PlotsWidget", u"1w", None))
#if QT_CONFIG(tooltip)
        self.last_month_button.setToolTip(QCoreApplication.translate("PlotsWidget", u"One month", None))
#endif // QT_CONFIG(tooltip)
        self.last_month_button.setText(QCoreApplication.translate("PlotsWidget", u"1m", None))
        self.tonight_button.setText(QCoreApplication.translate("PlotsWidget", u"Tonight", None))
        ___qtreewidgetitem = self.monitoring_treeview.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("PlotsWidget", u"Monitoring", None));
        ___qtreewidgetitem1 = self.obs_treeview.headerItem()
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("PlotsWidget", u"Observation", None));
        self.autoupdate_groupbox.setTitle(QCoreApplication.translate("PlotsWidget", u"Auto-update", None))
        self.autoupdate_checkbox.setText("")
        self.autoupdate_label.setText(QCoreApplication.translate("PlotsWidget", u"Enabled", None))
        self.autoupdate_refresh_rate_spinbox.setSuffix(QCoreApplication.translate("PlotsWidget", u" s", None))
        self.autoupdate_database_button.setText("")
        self.autoupdate_direct_button.setText("")
        self.autoupdate_database_label.setText(QCoreApplication.translate("PlotsWidget", u"From database", None))
        self.autoupdate_refresh_rate_label.setText(QCoreApplication.translate("PlotsWidget", u"Refresh rate", None))
        self.autoupdate_direct_label.setText(QCoreApplication.translate("PlotsWidget", u"Real-time data", None))
        self.clear_all_button.setText(QCoreApplication.translate("PlotsWidget", u"Clear all", None))
        self.plot_button.setText(QCoreApplication.translate("PlotsWidget", u"Plot", None))
    # retranslateUi

