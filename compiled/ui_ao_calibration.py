# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ao_calibration.ui'
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
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStatusBar, QTabWidget, QToolButton, QVBoxLayout,
    QWidget)

from kalao.guis.utils.widgets import (KChartView, KImageViewer, KLabel, KNaNDoubleSpinbox,
    KStatusIndicator)
from . import rc_assets

class Ui_AOCalibrationWindow(object):
    def setupUi(self, AOCalibrationWindow):
        if not AOCalibrationWindow.objectName():
            AOCalibrationWindow.setObjectName(u"AOCalibrationWindow")
        AOCalibrationWindow.resize(1102, 553)
        self.centralwidget = QWidget(AOCalibrationWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.calibration_layout = QGridLayout()
        self.calibration_layout.setObjectName(u"calibration_layout")
        self.calibration_loopname_label = KLabel(self.centralwidget)
        self.calibration_loopname_label.setObjectName(u"calibration_loopname_label")

        self.calibration_layout.addWidget(self.calibration_loopname_label, 0, 0, 1, 2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.calibration_layout.addItem(self.verticalSpacer_2, 2, 0, 1, 2)

        self.calibration_loopnumber_label = KLabel(self.centralwidget)
        self.calibration_loopnumber_label.setObjectName(u"calibration_loopnumber_label")

        self.calibration_layout.addWidget(self.calibration_loopnumber_label, 1, 0, 1, 2)

        self.calibration_buttons_widget = QWidget(self.centralwidget)
        self.calibration_buttons_widget.setObjectName(u"calibration_buttons_widget")
        self.gridLayout_4 = QGridLayout(self.calibration_buttons_widget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.calibration_compCM_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_compCM_indicator.setObjectName(u"calibration_compCM_indicator")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.calibration_compCM_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_compCM_indicator.setSizePolicy(sizePolicy)
        self.calibration_compCM_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_compCM_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_compCM_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_compCM_indicator, 7, 0, 1, 1)

        self.calibration_RMmkmask_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_RMmkmask_button.setObjectName(u"calibration_RMmkmask_button")
        self.calibration_RMmkmask_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_RMmkmask_button, 6, 1, 1, 1)

        self.calibration_RMmkmask_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_RMmkmask_indicator.setObjectName(u"calibration_RMmkmask_indicator")
        sizePolicy.setHeightForWidth(self.calibration_RMmkmask_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_RMmkmask_indicator.setSizePolicy(sizePolicy)
        self.calibration_RMmkmask_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_RMmkmask_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_RMmkmask_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_RMmkmask_indicator, 6, 0, 1, 1)

        self.calibration_RMHdecode_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_RMHdecode_indicator.setObjectName(u"calibration_RMHdecode_indicator")
        sizePolicy.setHeightForWidth(self.calibration_RMHdecode_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_RMHdecode_indicator.setSizePolicy(sizePolicy)
        self.calibration_RMHdecode_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_RMHdecode_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_RMHdecode_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_RMHdecode_indicator, 5, 0, 1, 1)

        self.calibration_takeref_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_takeref_indicator.setObjectName(u"calibration_takeref_indicator")
        sizePolicy.setHeightForWidth(self.calibration_takeref_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_takeref_indicator.setSizePolicy(sizePolicy)
        self.calibration_takeref_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_takeref_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_takeref_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_takeref_indicator, 3, 0, 1, 1)

        self.calibration_load_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_load_button.setObjectName(u"calibration_load_button")
        self.calibration_load_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_load_button, 8, 1, 1, 1)

        self.calibration_mlat_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_mlat_button.setObjectName(u"calibration_mlat_button")
        self.calibration_mlat_button.setEnabled(False)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.calibration_mlat_button.sizePolicy().hasHeightForWidth())
        self.calibration_mlat_button.setSizePolicy(sizePolicy1)

        self.gridLayout_4.addWidget(self.calibration_mlat_button, 1, 1, 1, 1)

        self.calibration_compCM_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_compCM_button.setObjectName(u"calibration_compCM_button")
        self.calibration_compCM_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_compCM_button, 7, 1, 1, 1)

        self.calibration_acqlinResp_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_acqlinResp_indicator.setObjectName(u"calibration_acqlinResp_indicator")
        sizePolicy.setHeightForWidth(self.calibration_acqlinResp_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_acqlinResp_indicator.setSizePolicy(sizePolicy)
        self.calibration_acqlinResp_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_acqlinResp_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_acqlinResp_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_acqlinResp_indicator, 4, 0, 1, 1)

        self.calibration_mkDMpokemodes_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_mkDMpokemodes_button.setObjectName(u"calibration_mkDMpokemodes_button")
        self.calibration_mkDMpokemodes_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_mkDMpokemodes_button, 2, 1, 1, 1)

        self.calibration_takeref_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_takeref_button.setObjectName(u"calibration_takeref_button")
        self.calibration_takeref_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_takeref_button, 3, 1, 1, 1)

        self.calibration_RMHdecode_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_RMHdecode_button.setObjectName(u"calibration_RMHdecode_button")
        self.calibration_RMHdecode_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_RMHdecode_button, 5, 1, 1, 1)

        self.calibration_prepare_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_prepare_indicator.setObjectName(u"calibration_prepare_indicator")
        sizePolicy.setHeightForWidth(self.calibration_prepare_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_prepare_indicator.setSizePolicy(sizePolicy)
        self.calibration_prepare_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_prepare_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_prepare_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_prepare_indicator, 0, 0, 1, 1)

        self.calibration_prepare_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_prepare_button.setObjectName(u"calibration_prepare_button")

        self.gridLayout_4.addWidget(self.calibration_prepare_button, 0, 1, 1, 1)

        self.calibration_acqlinResp_button = QPushButton(self.calibration_buttons_widget)
        self.calibration_acqlinResp_button.setObjectName(u"calibration_acqlinResp_button")
        self.calibration_acqlinResp_button.setEnabled(False)

        self.gridLayout_4.addWidget(self.calibration_acqlinResp_button, 4, 1, 1, 1)

        self.calibration_load_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_load_indicator.setObjectName(u"calibration_load_indicator")
        sizePolicy.setHeightForWidth(self.calibration_load_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_load_indicator.setSizePolicy(sizePolicy)
        self.calibration_load_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_load_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_load_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_load_indicator, 8, 0, 1, 1)

        self.calibration_mkDMpokemodes_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_mkDMpokemodes_indicator.setObjectName(u"calibration_mkDMpokemodes_indicator")
        sizePolicy.setHeightForWidth(self.calibration_mkDMpokemodes_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_mkDMpokemodes_indicator.setSizePolicy(sizePolicy)
        self.calibration_mkDMpokemodes_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_mkDMpokemodes_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_mkDMpokemodes_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_mkDMpokemodes_indicator, 2, 0, 1, 1)

        self.calibration_mlat_indicator = KStatusIndicator(self.calibration_buttons_widget)
        self.calibration_mlat_indicator.setObjectName(u"calibration_mlat_indicator")
        sizePolicy.setHeightForWidth(self.calibration_mlat_indicator.sizePolicy().hasHeightForWidth())
        self.calibration_mlat_indicator.setSizePolicy(sizePolicy)
        self.calibration_mlat_indicator.setMinimumSize(QSize(20, 20))
        self.calibration_mlat_indicator.setMaximumSize(QSize(20, 20))
        self.calibration_mlat_indicator.viewport().setProperty("cursor", QCursor(Qt.CursorShape.WhatsThisCursor))

        self.gridLayout_4.addWidget(self.calibration_mlat_indicator, 1, 0, 1, 1)

        self.calibration_save_restore_widget = QWidget(self.calibration_buttons_widget)
        self.calibration_save_restore_widget.setObjectName(u"calibration_save_restore_widget")
        self.calibration_save_restore_widget.setEnabled(False)
        self.gridLayout_7 = QGridLayout(self.calibration_save_restore_widget)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.calibration_restore_button = QPushButton(self.calibration_save_restore_widget)
        self.calibration_restore_button.setObjectName(u"calibration_restore_button")

        self.gridLayout_7.addWidget(self.calibration_restore_button, 0, 1, 1, 1)

        self.calibration_save_button = QPushButton(self.calibration_save_restore_widget)
        self.calibration_save_button.setObjectName(u"calibration_save_button")

        self.gridLayout_7.addWidget(self.calibration_save_button, 0, 0, 1, 1)

        self.calibration_comment_lineedit = QLineEdit(self.calibration_save_restore_widget)
        self.calibration_comment_lineedit.setObjectName(u"calibration_comment_lineedit")

        self.gridLayout_7.addWidget(self.calibration_comment_lineedit, 1, 0, 1, 2)


        self.gridLayout_4.addWidget(self.calibration_save_restore_widget, 9, 0, 1, 2)


        self.calibration_layout.addWidget(self.calibration_buttons_widget, 3, 0, 1, 1)


        self.horizontalLayout.addLayout(self.calibration_layout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.calibration_tab = QWidget()
        self.calibration_tab.setObjectName(u"calibration_tab")
        self.gridLayout_2 = QGridLayout(self.calibration_tab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.dmmap_label = QLabel(self.calibration_tab)
        self.dmmap_label.setObjectName(u"dmmap_label")
        font = QFont()
        font.setBold(True)
        self.dmmap_label.setFont(font)
        self.dmmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.dmmap_label, 2, 0, 1, 1)

        self.wfsrefc_label = QLabel(self.calibration_tab)
        self.wfsrefc_label.setObjectName(u"wfsrefc_label")
        self.wfsrefc_label.setFont(font)
        self.wfsrefc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.wfsrefc_label, 0, 3, 1, 1)

        self.wfsmap_view = KImageViewer(self.calibration_tab)
        self.wfsmap_view.setObjectName(u"wfsmap_view")
        self.wfsmap_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.wfsmap_view, 1, 0, 1, 1)

        self.wfsrefc_view = KImageViewer(self.calibration_tab)
        self.wfsrefc_view.setObjectName(u"wfsrefc_view")
        self.wfsrefc_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.wfsrefc_view, 1, 3, 1, 1)

        self.wfsmask_view = KImageViewer(self.calibration_tab)
        self.wfsmask_view.setObjectName(u"wfsmask_view")
        self.wfsmask_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.wfsmask_view, 1, 1, 1, 1)

        self.wfsrerf_label = QLabel(self.calibration_tab)
        self.wfsrerf_label.setObjectName(u"wfsrerf_label")
        self.wfsrerf_label.setFont(font)
        self.wfsrerf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.wfsrerf_label, 0, 4, 1, 1)

        self.wfsmask_label = QLabel(self.calibration_tab)
        self.wfsmask_label.setObjectName(u"wfsmask_label")
        self.wfsmask_label.setFont(font)
        self.wfsmask_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.wfsmask_label, 0, 1, 1, 1)

        self.modesWFS_view = KImageViewer(self.calibration_tab)
        self.modesWFS_view.setObjectName(u"modesWFS_view")
        self.modesWFS_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.modesWFS_view, 1, 2, 1, 1)

        self.modesWFS_label = QLabel(self.calibration_tab)
        self.modesWFS_label.setObjectName(u"modesWFS_label")
        self.modesWFS_label.setFont(font)
        self.modesWFS_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.modesWFS_label, 0, 2, 1, 1)

        self.wfsref_view = KImageViewer(self.calibration_tab)
        self.wfsref_view.setObjectName(u"wfsref_view")
        self.wfsref_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.wfsref_view, 1, 4, 1, 1)

        self.wfsmap_label = QLabel(self.calibration_tab)
        self.wfsmap_label.setObjectName(u"wfsmap_label")
        self.wfsmap_label.setFont(font)
        self.wfsmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.wfsmap_label, 0, 0, 1, 1)

        self.dmmap_view = KImageViewer(self.calibration_tab)
        self.dmmap_view.setObjectName(u"dmmap_view")
        self.dmmap_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.dmmap_view, 3, 0, 1, 1)

        self.dmmask_label = QLabel(self.calibration_tab)
        self.dmmask_label.setObjectName(u"dmmask_label")
        self.dmmask_label.setFont(font)
        self.dmmask_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.dmmask_label, 2, 1, 1, 1)

        self.dmmask_view = KImageViewer(self.calibration_tab)
        self.dmmask_view.setObjectName(u"dmmask_view")
        self.dmmask_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.dmmask_view, 3, 1, 1, 1)

        self.DMmodes_view = KImageViewer(self.calibration_tab)
        self.DMmodes_view.setObjectName(u"DMmodes_view")
        self.DMmodes_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.DMmodes_view, 3, 2, 1, 1)

        self.DMmodes_label = QLabel(self.calibration_tab)
        self.DMmodes_label.setObjectName(u"DMmodes_label")
        self.DMmodes_label.setFont(font)
        self.DMmodes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.DMmodes_label, 2, 2, 1, 1)

        self.modes_widget = QWidget(self.calibration_tab)
        self.modes_widget.setObjectName(u"modes_widget")
        self.verticalLayout_2 = QVBoxLayout(self.modes_widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.minmax_checkbox = QCheckBox(self.modes_widget)
        self.minmax_checkbox.setObjectName(u"minmax_checkbox")

        self.verticalLayout_2.addWidget(self.minmax_checkbox)

        self.calib_combobox = QComboBox(self.modes_widget)
        self.calib_combobox.setObjectName(u"calib_combobox")

        self.verticalLayout_2.addWidget(self.calib_combobox)

        self.mode_spinbox = QSpinBox(self.modes_widget)
        self.mode_spinbox.setObjectName(u"mode_spinbox")
        self.mode_spinbox.setKeyboardTracking(False)
        self.mode_spinbox.setMinimum(1)
        self.mode_spinbox.setMaximum(9999)

        self.verticalLayout_2.addWidget(self.mode_spinbox)

        self.all_modes_button = QPushButton(self.modes_widget)
        self.all_modes_button.setObjectName(u"all_modes_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/show-grid.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.all_modes_button.setIcon(icon)

        self.verticalLayout_2.addWidget(self.all_modes_button)

        self.refresh_button = QPushButton(self.modes_widget)
        self.refresh_button.setObjectName(u"refresh_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/refreshstructure.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.refresh_button.setIcon(icon1)

        self.verticalLayout_2.addWidget(self.refresh_button)

        self.reload_button = QPushButton(self.modes_widget)
        self.reload_button.setObjectName(u"reload_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/upload-media.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.reload_button.setIcon(icon2)

        self.verticalLayout_2.addWidget(self.reload_button)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)


        self.gridLayout_2.addWidget(self.modes_widget, 3, 3, 1, 2)

        self.tabWidget.addTab(self.calibration_tab, "")
        self.latency_tab = QWidget()
        self.latency_tab.setObjectName(u"latency_tab")
        self.gridLayout_3 = QGridLayout(self.latency_tab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.latency_framerate_label = QLabel(self.latency_tab)
        self.latency_framerate_label.setObjectName(u"latency_framerate_label")
        self.latency_framerate_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.latency_framerate_label, 1, 0, 1, 1)

        self.latency_frames_label = QLabel(self.latency_tab)
        self.latency_frames_label.setObjectName(u"latency_frames_label")
        self.latency_frames_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.latency_frames_label, 2, 0, 1, 1)

        self.latency_framerate_spinbox = KNaNDoubleSpinbox(self.latency_tab)
        self.latency_framerate_spinbox.setObjectName(u"latency_framerate_spinbox")
        self.latency_framerate_spinbox.setReadOnly(True)
        self.latency_framerate_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.latency_framerate_spinbox.setMaximum(10000.000000000000000)

        self.gridLayout_3.addWidget(self.latency_framerate_spinbox, 1, 1, 1, 1)

        self.latency_frames_spinbox = KNaNDoubleSpinbox(self.latency_tab)
        self.latency_frames_spinbox.setObjectName(u"latency_frames_spinbox")
        self.latency_frames_spinbox.setReadOnly(True)
        self.latency_frames_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.latency_frames_spinbox.setMaximum(100.000000000000000)

        self.gridLayout_3.addWidget(self.latency_frames_spinbox, 2, 1, 1, 1)

        self.latency_plot = KChartView(self.latency_tab)
        self.latency_plot.setObjectName(u"latency_plot")

        self.gridLayout_3.addWidget(self.latency_plot, 0, 0, 1, 2)

        self.gridLayout_3.setColumnStretch(1, 1)
        self.tabWidget.addTab(self.latency_tab, "")
        self.zRM_tab = QWidget()
        self.zRM_tab.setObjectName(u"zRM_tab")
        self.gridLayout = QGridLayout(self.zRM_tab)
        self.gridLayout.setObjectName(u"gridLayout")
        self.zRM_play_button = QToolButton(self.zRM_tab)
        self.zRM_play_button.setObjectName(u"zRM_play_button")
        self.zRM_play_button.setCheckable(True)

        self.gridLayout.addWidget(self.zRM_play_button, 1, 2, 1, 1)

        self.zRM_view = KImageViewer(self.zRM_tab)
        self.zRM_view.setObjectName(u"zRM_view")
        self.zRM_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout.addWidget(self.zRM_view, 0, 0, 1, 3)

        self.zRM_poke_spinbox = QSpinBox(self.zRM_tab)
        self.zRM_poke_spinbox.setObjectName(u"zRM_poke_spinbox")
        self.zRM_poke_spinbox.setKeyboardTracking(False)
        self.zRM_poke_spinbox.setMinimum(1)
        self.zRM_poke_spinbox.setMaximum(9999)

        self.gridLayout.addWidget(self.zRM_poke_spinbox, 1, 0, 1, 1)

        self.zRM_minmax_checkbox = QCheckBox(self.zRM_tab)
        self.zRM_minmax_checkbox.setObjectName(u"zRM_minmax_checkbox")

        self.gridLayout.addWidget(self.zRM_minmax_checkbox, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.tabWidget.addTab(self.zRM_tab, "")
        self.logs_tab = QWidget()
        self.logs_tab.setObjectName(u"logs_tab")
        self.verticalLayout_3 = QVBoxLayout(self.logs_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.calibration_textedit = QPlainTextEdit(self.logs_tab)
        self.calibration_textedit.setObjectName(u"calibration_textedit")
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
        self.calibration_textedit.setPalette(palette)
        font1 = QFont()
        font1.setFamilies([u"Roboto Mono"])
        self.calibration_textedit.setFont(font1)
        self.calibration_textedit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.calibration_textedit.setReadOnly(True)
        self.calibration_textedit.setCursorWidth(0)

        self.verticalLayout_3.addWidget(self.calibration_textedit)

        self.tabWidget.addTab(self.logs_tab, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        AOCalibrationWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(AOCalibrationWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1102, 30))
        AOCalibrationWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(AOCalibrationWindow)
        self.statusbar.setObjectName(u"statusbar")
        AOCalibrationWindow.setStatusBar(self.statusbar)

        self.retranslateUi(AOCalibrationWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AOCalibrationWindow)
    # setupUi

    def retranslateUi(self, AOCalibrationWindow):
        AOCalibrationWindow.setWindowTitle(QCoreApplication.translate("AOCalibrationWindow", u"AO Calibration - KalAO", None))
        self.calibration_loopname_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"Loop name: {loop_name}", None))
        self.calibration_loopnumber_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"Loop number: {loop_number:02d}", None))
        self.calibration_RMmkmask_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Compute DM and WFS maps and masks", None))
        self.calibration_load_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Load new calibration", None))
        self.calibration_mlat_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Measure latency", None))
        self.calibration_compCM_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Compute Control Matrix (CM)", None))
        self.calibration_mkDMpokemodes_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Make DM poke modes", None))
        self.calibration_takeref_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Take reference", None))
        self.calibration_RMHdecode_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Decode Hadamard Response Matrix (RM)", None))
        self.calibration_prepare_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Prepare for calibration", None))
        self.calibration_acqlinResp_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Measure WFS response to DM modes", None))
        self.calibration_restore_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Restore old calibration", None))
        self.calibration_save_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Save new calibration", None))
        self.calibration_comment_lineedit.setPlaceholderText(QCoreApplication.translate("AOCalibrationWindow", u"Optional comment ...", None))
        self.dmmap_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"DM Map", None))
        self.wfsrefc_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"WFS Reference C", None))
        self.wfsrerf_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"WFS Reference", None))
        self.wfsmask_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"WFS Mask", None))
        self.modesWFS_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"WFS Modes", None))
        self.wfsmap_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"WFS Map", None))
        self.dmmask_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"DM Mask", None))
        self.DMmodes_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"DM Modes", None))
        self.minmax_checkbox.setText(QCoreApplication.translate("AOCalibrationWindow", u"Per mode Min \u2013 Max", None))
        self.mode_spinbox.setSuffix(QCoreApplication.translate("AOCalibrationWindow", u" / --", None))
        self.mode_spinbox.setPrefix(QCoreApplication.translate("AOCalibrationWindow", u"Mode ", None))
        self.all_modes_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Show all modes in one window", None))
        self.refresh_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Refresh", None))
        self.reload_button.setText(QCoreApplication.translate("AOCalibrationWindow", u"Reload saved calibration", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.calibration_tab), QCoreApplication.translate("AOCalibrationWindow", u"Calibration", None))
        self.latency_framerate_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"Framerate", None))
        self.latency_frames_label.setText(QCoreApplication.translate("AOCalibrationWindow", u"Latency", None))
        self.latency_framerate_spinbox.setSuffix(QCoreApplication.translate("AOCalibrationWindow", u" Hz", None))
        self.latency_frames_spinbox.setSuffix(QCoreApplication.translate("AOCalibrationWindow", u" frames", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.latency_tab), QCoreApplication.translate("AOCalibrationWindow", u"Latency", None))
        self.zRM_play_button.setText("")
        self.zRM_poke_spinbox.setSuffix(QCoreApplication.translate("AOCalibrationWindow", u" / --", None))
        self.zRM_poke_spinbox.setPrefix(QCoreApplication.translate("AOCalibrationWindow", u"Poke ", None))
        self.zRM_minmax_checkbox.setText(QCoreApplication.translate("AOCalibrationWindow", u"Per poke Min \u2013 Max", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.zRM_tab), QCoreApplication.translate("AOCalibrationWindow", u"Zonal Response Matrix", None))
        self.calibration_textedit.setPlaceholderText(QCoreApplication.translate("AOCalibrationWindow", u"Logs will appear here ...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.logs_tab), QCoreApplication.translate("AOCalibrationWindow", u"Logs", None))
    # retranslateUi

