# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fits_viewer.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QSpinBox, QSplitter,
    QStatusBar, QTableView, QToolButton, QVBoxLayout,
    QWidget)

from kalao.guis.utils.widgets import (KColorbar, KImageViewer, KLabel, KScaledDoubleSpinbox)
from . import rc_assets

class Ui_FITSViewerWindow(object):
    def setupUi(self, FITSViewerWindow):
        if not FITSViewerWindow.objectName():
            FITSViewerWindow.setObjectName(u"FITSViewerWindow")
        FITSViewerWindow.resize(1554, 680)
        self.enter_manual_centering_action = QAction(FITSViewerWindow)
        self.enter_manual_centering_action.setObjectName(u"enter_manual_centering_action")
        icon = QIcon()
        icon.addFile(u":/assets/icons/crosshairs.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.enter_manual_centering_action.setIcon(icon)
        self.centralwidget = QWidget(FITSViewerWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.keywords_splitter = QSplitter(self.centralwidget)
        self.keywords_splitter.setObjectName(u"keywords_splitter")
        self.keywords_splitter.setOrientation(Qt.Orientation.Vertical)
        self.keywords_splitter.setHandleWidth(10)
        self.keywords_splitter.setChildrenCollapsible(False)
        self.gridLayoutWidget = QWidget(self.keywords_splitter)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayout_2 = QGridLayout(self.gridLayoutWidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.zoom_title_label = QLabel(self.gridLayoutWidget)
        self.zoom_title_label.setObjectName(u"zoom_title_label")
        font = QFont()
        font.setBold(True)
        self.zoom_title_label.setFont(font)
        self.zoom_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.zoom_title_label, 0, 2, 1, 1)

        self.title_label = QLabel(self.gridLayoutWidget)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.title_label, 0, 1, 1, 1)

        self.colorbar = KColorbar(self.gridLayoutWidget)
        self.colorbar.setObjectName(u"colorbar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorbar.sizePolicy().hasHeightForWidth())
        self.colorbar.setSizePolicy(sizePolicy)
        self.colorbar.setMinimumSize(QSize(95, 0))
        self.colorbar.setMaximumSize(QSize(95, 16777215))
        self.colorbar.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.colorbar, 1, 3, 1, 1)

        self.zoom_view = KImageViewer(self.gridLayoutWidget)
        self.zoom_view.setObjectName(u"zoom_view")
        self.zoom_view.setFrameShape(QFrame.Shape.NoFrame)

        self.gridLayout_2.addWidget(self.zoom_view, 1, 2, 1, 1)

        self.image_view = KImageViewer(self.gridLayoutWidget)
        self.image_view.setObjectName(u"image_view")
        self.image_view.setEnabled(True)
        self.image_view.setFrameShape(QFrame.Shape.NoFrame)
        self.image_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout_2.addWidget(self.image_view, 1, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.scale_layout = QGridLayout()
        self.scale_layout.setObjectName(u"scale_layout")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scale_layout.addItem(self.verticalSpacer_3, 1, 0, 1, 3)

        self.y_label = QLabel(self.gridLayoutWidget)
        self.y_label.setObjectName(u"y_label")
        self.y_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.scale_layout.addWidget(self.y_label, 3, 0, 1, 1)

        self.x_label = QLabel(self.gridLayoutWidget)
        self.x_label.setObjectName(u"x_label")
        self.x_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.scale_layout.addWidget(self.x_label, 2, 0, 1, 1)

        self.zoom_label = QLabel(self.gridLayoutWidget)
        self.zoom_label.setObjectName(u"zoom_label")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.scale_layout.addWidget(self.zoom_label, 4, 0, 1, 1)

        self.frame_label = QLabel(self.gridLayoutWidget)
        self.frame_label.setObjectName(u"frame_label")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.scale_layout.addWidget(self.frame_label, 5, 0, 1, 1)

        self.frame_slider = QSlider(self.gridLayoutWidget)
        self.frame_slider.setObjectName(u"frame_slider")
        self.frame_slider.setMinimum(1)
        self.frame_slider.setMaximum(1)
        self.frame_slider.setOrientation(Qt.Orientation.Horizontal)

        self.scale_layout.addWidget(self.frame_slider, 5, 1, 1, 1)

        self.zoom_spinbox = QSpinBox(self.gridLayoutWidget)
        self.zoom_spinbox.setObjectName(u"zoom_spinbox")
        self.zoom_spinbox.setReadOnly(True)
        self.zoom_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.zoom_spinbox.setKeyboardTracking(False)
        self.zoom_spinbox.setMinimum(1)
        self.zoom_spinbox.setMaximum(1024)
        self.zoom_spinbox.setStepType(QAbstractSpinBox.StepType.DefaultStepType)
        self.zoom_spinbox.setValue(1)

        self.scale_layout.addWidget(self.zoom_spinbox, 4, 1, 1, 2)

        self.frame_spinbox = QSpinBox(self.gridLayoutWidget)
        self.frame_spinbox.setObjectName(u"frame_spinbox")
        self.frame_spinbox.setKeyboardTracking(False)
        self.frame_spinbox.setMinimum(1)
        self.frame_spinbox.setMaximum(1)

        self.scale_layout.addWidget(self.frame_spinbox, 5, 2, 1, 1)

        self.y_spinbox = KScaledDoubleSpinbox(self.gridLayoutWidget)
        self.y_spinbox.setObjectName(u"y_spinbox")
        self.y_spinbox.setReadOnly(True)
        self.y_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.y_spinbox.setKeyboardTracking(False)
        self.y_spinbox.setDecimals(0)
        self.y_spinbox.setMinimum(-9999.000000000000000)
        self.y_spinbox.setMaximum(9999.000000000000000)

        self.scale_layout.addWidget(self.y_spinbox, 3, 1, 1, 2)

        self.x_spinbox = KScaledDoubleSpinbox(self.gridLayoutWidget)
        self.x_spinbox.setObjectName(u"x_spinbox")
        self.x_spinbox.setReadOnly(True)
        self.x_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.x_spinbox.setKeyboardTracking(False)
        self.x_spinbox.setDecimals(0)
        self.x_spinbox.setMinimum(-9999.000000000000000)
        self.x_spinbox.setMaximum(9999.000000000000000)

        self.scale_layout.addWidget(self.x_spinbox, 2, 1, 1, 2)

        self.scale_layout_2 = QGridLayout()
        self.scale_layout_2.setObjectName(u"scale_layout_2")
        self.saturation_label = KLabel(self.gridLayoutWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scale_layout_2.addWidget(self.saturation_label, 2, 0, 1, 3, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.min_spinbox = KScaledDoubleSpinbox(self.gridLayoutWidget)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setKeyboardTracking(False)
        self.min_spinbox.setDecimals(0)
        self.min_spinbox.setMinimum(0.000000000000000)
        self.min_spinbox.setMaximum(100000.000000000000000)
        self.min_spinbox.setSingleStep(100.000000000000000)

        self.scale_layout_2.addWidget(self.min_spinbox, 1, 0, 1, 1)

        self.max_spinbox = KScaledDoubleSpinbox(self.gridLayoutWidget)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setKeyboardTracking(False)
        self.max_spinbox.setDecimals(0)
        self.max_spinbox.setMinimum(0.000000000000000)
        self.max_spinbox.setMaximum(100000.000000000000000)
        self.max_spinbox.setSingleStep(100.000000000000000)

        self.scale_layout_2.addWidget(self.max_spinbox, 1, 2, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self.minmax_label = QLabel(self.gridLayoutWidget)
        self.minmax_label.setObjectName(u"minmax_label")

        self.scale_layout_2.addWidget(self.minmax_label, 1, 1, 1, 1)

        self.fullscale_button = QToolButton(self.gridLayoutWidget)
        self.fullscale_button.setObjectName(u"fullscale_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.fullscale_button.sizePolicy().hasHeightForWidth())
        self.fullscale_button.setSizePolicy(sizePolicy1)
        self.fullscale_button.setCheckable(True)

        self.scale_layout_2.addWidget(self.fullscale_button, 0, 2, 1, 1)

        self.autoscale_button = QToolButton(self.gridLayoutWidget)
        self.autoscale_button.setObjectName(u"autoscale_button")
        sizePolicy1.setHeightForWidth(self.autoscale_button.sizePolicy().hasHeightForWidth())
        self.autoscale_button.setSizePolicy(sizePolicy1)
        self.autoscale_button.setCheckable(True)
        self.autoscale_button.setChecked(True)

        self.scale_layout_2.addWidget(self.autoscale_button, 0, 0, 1, 1)

        self.scale_layout_2.setColumnStretch(0, 1)
        self.scale_layout_2.setColumnStretch(2, 1)

        self.scale_layout.addLayout(self.scale_layout_2, 0, 0, 1, 3)


        self.side_layout.addLayout(self.scale_layout)

        self.onsky_checkbox = QCheckBox(self.gridLayoutWidget)
        self.onsky_checkbox.setObjectName(u"onsky_checkbox")

        self.side_layout.addWidget(self.onsky_checkbox, 0, Qt.AlignmentFlag.AlignHCenter)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.timestamp_label = KLabel(self.gridLayoutWidget)
        self.timestamp_label.setObjectName(u"timestamp_label")
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.timestamp_label)

        self.star_x_label = KLabel(self.gridLayoutWidget)
        self.star_x_label.setObjectName(u"star_x_label")
        self.star_x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.star_x_label)

        self.star_y_label = KLabel(self.gridLayoutWidget)
        self.star_y_label.setObjectName(u"star_y_label")
        self.star_y_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.star_y_label)

        self.star_fwhm_label = KLabel(self.gridLayoutWidget)
        self.star_fwhm_label.setObjectName(u"star_fwhm_label")
        self.star_fwhm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.star_fwhm_label)

        self.star_peak_label = KLabel(self.gridLayoutWidget)
        self.star_peak_label.setObjectName(u"star_peak_label")
        self.star_peak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.star_peak_label)


        self.gridLayout_2.addLayout(self.side_layout, 0, 0, 3, 1)

        self.centering_widget = QWidget(self.gridLayoutWidget)
        self.centering_widget.setObjectName(u"centering_widget")
        self.gridLayout_3 = QGridLayout(self.centering_widget)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.centering_abort_button = QPushButton(self.centering_widget)
        self.centering_abort_button.setObjectName(u"centering_abort_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/emblem-error.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_abort_button.setIcon(icon1)

        self.gridLayout_3.addWidget(self.centering_abort_button, 0, 2, 1, 1)

        self.centering_exit_button = QPushButton(self.centering_widget)
        self.centering_exit_button.setObjectName(u"centering_exit_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/emblem-checked.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_exit_button.setIcon(icon2)

        self.gridLayout_3.addWidget(self.centering_exit_button, 0, 1, 1, 1)

        self.centering_volume_button = QToolButton(self.centering_widget)
        self.centering_volume_button.setObjectName(u"centering_volume_button")
        self.centering_volume_button.setCheckable(True)

        self.gridLayout_3.addWidget(self.centering_volume_button, 0, 0, 1, 1)

        self.centering_reason_label = KLabel(self.centering_widget)
        self.centering_reason_label.setObjectName(u"centering_reason_label")
        self.centering_reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.centering_reason_label, 1, 1, 1, 1)

        self.centering_timeout_label = KLabel(self.centering_widget)
        self.centering_timeout_label.setObjectName(u"centering_timeout_label")
        self.centering_timeout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.centering_timeout_label, 1, 2, 1, 1)


        self.gridLayout_2.addWidget(self.centering_widget, 2, 1, 1, 2)

        self.gridLayout_2.setColumnStretch(1, 1)
        self.gridLayout_2.setColumnStretch(2, 1)
        self.keywords_splitter.addWidget(self.gridLayoutWidget)
        self.layoutWidget = QWidget(self.keywords_splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.keywords_button_widget = QWidget(self.layoutWidget)
        self.keywords_button_widget.setObjectName(u"keywords_button_widget")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.keywords_button_widget.sizePolicy().hasHeightForWidth())
        self.keywords_button_widget.setSizePolicy(sizePolicy2)
        self.horizontalLayout_2 = QHBoxLayout(self.keywords_button_widget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.keywords_toolbutton = QToolButton(self.keywords_button_widget)
        self.keywords_toolbutton.setObjectName(u"keywords_toolbutton")
        self.keywords_toolbutton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.keywords_toolbutton.setStyleSheet(u"border: none")
        self.keywords_toolbutton.setCheckable(True)
        self.keywords_toolbutton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.keywords_toolbutton.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout_2.addWidget(self.keywords_toolbutton)

        self.keywords_separator = QFrame(self.keywords_button_widget)
        self.keywords_separator.setObjectName(u"keywords_separator")
        self.keywords_separator.setFrameShape(QFrame.Shape.HLine)
        self.keywords_separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_2.addWidget(self.keywords_separator)


        self.verticalLayout.addWidget(self.keywords_button_widget)

        self.keywords_widget = QWidget(self.layoutWidget)
        self.keywords_widget.setObjectName(u"keywords_widget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.keywords_widget.sizePolicy().hasHeightForWidth())
        self.keywords_widget.setSizePolicy(sizePolicy3)
        self.verticalLayout_2 = QVBoxLayout(self.keywords_widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.keywords_filter_layout = QHBoxLayout()
        self.keywords_filter_layout.setObjectName(u"keywords_filter_layout")
        self.keywords_filter_lineedit = QLineEdit(self.keywords_widget)
        self.keywords_filter_lineedit.setObjectName(u"keywords_filter_lineedit")
        self.keywords_filter_lineedit.setClearButtonEnabled(True)

        self.keywords_filter_layout.addWidget(self.keywords_filter_lineedit)

        self.keywords_columns_combobox = QComboBox(self.keywords_widget)
        self.keywords_columns_combobox.addItem("")
        self.keywords_columns_combobox.setObjectName(u"keywords_columns_combobox")

        self.keywords_filter_layout.addWidget(self.keywords_columns_combobox)

        self.keywords_casesensitive_checkbox = QCheckBox(self.keywords_widget)
        self.keywords_casesensitive_checkbox.setObjectName(u"keywords_casesensitive_checkbox")

        self.keywords_filter_layout.addWidget(self.keywords_casesensitive_checkbox)


        self.verticalLayout_2.addLayout(self.keywords_filter_layout)

        self.keywords_table = QTableView(self.keywords_widget)
        self.keywords_table.setObjectName(u"keywords_table")
        self.keywords_table.setSortingEnabled(True)
        self.keywords_table.horizontalHeader().setStretchLastSection(True)
        self.keywords_table.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.keywords_table)


        self.verticalLayout.addWidget(self.keywords_widget)

        self.keywords_splitter.addWidget(self.layoutWidget)

        self.gridLayout.addWidget(self.keywords_splitter, 0, 0, 1, 1)

        FITSViewerWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(FITSViewerWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1554, 30))
        self.colormap_menu = QMenu(self.menubar)
        self.colormap_menu.setObjectName(u"colormap_menu")
        self.scale_menu = QMenu(self.menubar)
        self.scale_menu.setObjectName(u"scale_menu")
        self.cuts_menu = QMenu(self.menubar)
        self.cuts_menu.setObjectName(u"cuts_menu")
        self.zoomwindow_menu = QMenu(self.menubar)
        self.zoomwindow_menu.setObjectName(u"zoomwindow_menu")
        self.centering_menu = QMenu(self.menubar)
        self.centering_menu.setObjectName(u"centering_menu")
        FITSViewerWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(FITSViewerWindow)
        self.statusbar.setObjectName(u"statusbar")
        FITSViewerWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.colormap_menu.menuAction())
        self.menubar.addAction(self.scale_menu.menuAction())
        self.menubar.addAction(self.cuts_menu.menuAction())
        self.menubar.addAction(self.zoomwindow_menu.menuAction())
        self.menubar.addAction(self.centering_menu.menuAction())
        self.centering_menu.addAction(self.enter_manual_centering_action)

        self.retranslateUi(FITSViewerWindow)

        QMetaObject.connectSlotsByName(FITSViewerWindow)
    # setupUi

    def retranslateUi(self, FITSViewerWindow):
        FITSViewerWindow.setWindowTitle(QCoreApplication.translate("FITSViewerWindow", u"Science Camera - KalAO", None))
        self.enter_manual_centering_action.setText(QCoreApplication.translate("FITSViewerWindow", u"&Enter manual centering", None))
        self.zoom_title_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Zoom - Science Camera", None))
        self.title_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Science Camera", None))
        self.y_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Y", None))
        self.x_label.setText(QCoreApplication.translate("FITSViewerWindow", u"X", None))
        self.zoom_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Zoom", None))
        self.frame_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Frame", None))
        self.zoom_spinbox.setSuffix(QCoreApplication.translate("FITSViewerWindow", u" x", None))
        self.zoom_spinbox.setPrefix("")
        self.saturation_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Saturation {saturation:.0f} %", None))
        self.minmax_label.setText(QCoreApplication.translate("FITSViewerWindow", u"\u2013", None))
        self.fullscale_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Fullscale", None))
        self.autoscale_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Autoscale", None))
        self.onsky_checkbox.setText(QCoreApplication.translate("FITSViewerWindow", u"On-Sky Units", None))
        self.timestamp_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Timestamp: {timestamp}", None))
        self.star_x_label.setText(QCoreApplication.translate("FITSViewerWindow", u"X: {x:.{axis_precision}f}{axis_unit}", None))
        self.star_y_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Y: {y:.{axis_precision}f}{axis_unit}", None))
        self.star_fwhm_label.setText(QCoreApplication.translate("FITSViewerWindow", u"FWHM: {fwhm:.{axis_precision}f}{axis_unit}", None))
        self.star_peak_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Peak: {peak:.{data_precision}f}{data_unit}", None))
        self.centering_abort_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Abort observation", None))
        self.centering_exit_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Validate manual centering", None))
        self.centering_volume_button.setText("")
        self.centering_reason_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Reason: {reason}", None))
        self.centering_timeout_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Time left: {timeout:.0f} s", None))
        self.keywords_toolbutton.setText(QCoreApplication.translate("FITSViewerWindow", u"Keywords", None))
        self.keywords_filter_lineedit.setPlaceholderText(QCoreApplication.translate("FITSViewerWindow", u"Filter ...", None))
        self.keywords_columns_combobox.setItemText(0, QCoreApplication.translate("FITSViewerWindow", u"All columns", None))

        self.keywords_casesensitive_checkbox.setText(QCoreApplication.translate("FITSViewerWindow", u"Case sensitive", None))
        self.colormap_menu.setTitle(QCoreApplication.translate("FITSViewerWindow", u"Co&lormap", None))
        self.scale_menu.setTitle(QCoreApplication.translate("FITSViewerWindow", u"&Scale", None))
        self.cuts_menu.setTitle(QCoreApplication.translate("FITSViewerWindow", u"Cuts", None))
        self.zoomwindow_menu.setTitle(QCoreApplication.translate("FITSViewerWindow", u"&Zoom window", None))
        self.centering_menu.setTitle(QCoreApplication.translate("FITSViewerWindow", u"Cente&ring", None))
    # retranslateUi

