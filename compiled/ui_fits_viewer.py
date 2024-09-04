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

from kalao.guis.utils.parts import ImgMinMaxPart
from kalao.guis.utils.widgets import (KColorbar, KImageViewer, KLabel, KNaNDoubleSpinbox)
from . import rc_assets

class Ui_FITSViewerWindow(object):
    def setupUi(self, FITSViewerWindow):
        if not FITSViewerWindow.objectName():
            FITSViewerWindow.setObjectName(u"FITSViewerWindow")
        FITSViewerWindow.resize(1534, 968)
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
        self.minmax_widget = ImgMinMaxPart(self.gridLayoutWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(self.gridLayoutWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.side_layout.addItem(self.verticalSpacer_2)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.y_label = QLabel(self.gridLayoutWidget)
        self.y_label.setObjectName(u"y_label")
        self.y_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.y_label, 2, 0, 1, 1)

        self.frame_label = QLabel(self.gridLayoutWidget)
        self.frame_label.setObjectName(u"frame_label")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.frame_label, 6, 0, 1, 1)

        self.value_label = QLabel(self.gridLayoutWidget)
        self.value_label.setObjectName(u"value_label")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.value_label, 0, 0, 1, 1)

        self.y_spinbox = KNaNDoubleSpinbox(self.gridLayoutWidget)
        self.y_spinbox.setObjectName(u"y_spinbox")
        self.y_spinbox.setReadOnly(True)
        self.y_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.y_spinbox.setKeyboardTracking(False)
        self.y_spinbox.setDecimals(0)
        self.y_spinbox.setMinimum(-9999.000000000000000)
        self.y_spinbox.setMaximum(9999.000000000000000)

        self.gridLayout_4.addWidget(self.y_spinbox, 2, 1, 1, 1)

        self.value_spinbox = KNaNDoubleSpinbox(self.gridLayoutWidget)
        self.value_spinbox.setObjectName(u"value_spinbox")
        self.value_spinbox.setReadOnly(True)
        self.value_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.value_spinbox.setKeyboardTracking(False)
        self.value_spinbox.setDecimals(0)
        self.value_spinbox.setMinimum(-9999.000000000000000)
        self.value_spinbox.setMaximum(9999.000000000000000)

        self.gridLayout_4.addWidget(self.value_spinbox, 0, 1, 1, 1)

        self.x_spinbox = KNaNDoubleSpinbox(self.gridLayoutWidget)
        self.x_spinbox.setObjectName(u"x_spinbox")
        self.x_spinbox.setReadOnly(True)
        self.x_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.x_spinbox.setKeyboardTracking(False)
        self.x_spinbox.setDecimals(0)
        self.x_spinbox.setMinimum(-9999.000000000000000)
        self.x_spinbox.setMaximum(9999.000000000000000)

        self.gridLayout_4.addWidget(self.x_spinbox, 1, 1, 1, 1)

        self.wcs_1_label = KLabel(self.gridLayoutWidget)
        self.wcs_1_label.setObjectName(u"wcs_1_label")
        self.wcs_1_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.wcs_1_label, 3, 0, 1, 1)

        self.wcs_1_lineedit = QLineEdit(self.gridLayoutWidget)
        self.wcs_1_lineedit.setObjectName(u"wcs_1_lineedit")
        self.wcs_1_lineedit.setReadOnly(True)

        self.gridLayout_4.addWidget(self.wcs_1_lineedit, 3, 1, 1, 1)

        self.x_label = QLabel(self.gridLayoutWidget)
        self.x_label.setObjectName(u"x_label")
        self.x_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.x_label, 1, 0, 1, 1)

        self.wcs_2_label = KLabel(self.gridLayoutWidget)
        self.wcs_2_label.setObjectName(u"wcs_2_label")
        self.wcs_2_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.wcs_2_label, 4, 0, 1, 1)

        self.wcs_2_lineedit = QLineEdit(self.gridLayoutWidget)
        self.wcs_2_lineedit.setObjectName(u"wcs_2_lineedit")
        self.wcs_2_lineedit.setReadOnly(True)

        self.gridLayout_4.addWidget(self.wcs_2_lineedit, 4, 1, 1, 1)

        self.wcs_system_label = QLabel(self.gridLayoutWidget)
        self.wcs_system_label.setObjectName(u"wcs_system_label")
        self.wcs_system_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_4.addWidget(self.wcs_system_label, 5, 0, 1, 1)

        self.wcs_system_lineedit = QLineEdit(self.gridLayoutWidget)
        self.wcs_system_lineedit.setObjectName(u"wcs_system_lineedit")
        self.wcs_system_lineedit.setReadOnly(True)

        self.gridLayout_4.addWidget(self.wcs_system_lineedit, 5, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame_slider = QSlider(self.gridLayoutWidget)
        self.frame_slider.setObjectName(u"frame_slider")
        self.frame_slider.setMinimum(1)
        self.frame_slider.setMaximum(1)
        self.frame_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout.addWidget(self.frame_slider)

        self.frame_spinbox = QSpinBox(self.gridLayoutWidget)
        self.frame_spinbox.setObjectName(u"frame_spinbox")
        self.frame_spinbox.setKeyboardTracking(False)
        self.frame_spinbox.setMinimum(1)
        self.frame_spinbox.setMaximum(1)

        self.horizontalLayout.addWidget(self.frame_spinbox)


        self.gridLayout_4.addLayout(self.horizontalLayout, 6, 1, 1, 1)

        self.relative_coord_checkbox = QCheckBox(self.gridLayoutWidget)
        self.relative_coord_checkbox.setObjectName(u"relative_coord_checkbox")

        self.gridLayout_4.addWidget(self.relative_coord_checkbox, 7, 1, 1, 1)


        self.side_layout.addLayout(self.gridLayout_4)

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
        self.centering_timeout_label = KLabel(self.centering_widget)
        self.centering_timeout_label.setObjectName(u"centering_timeout_label")
        self.centering_timeout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.centering_timeout_label, 2, 2, 1, 1)

        self.centering_validate_button = QPushButton(self.centering_widget)
        self.centering_validate_button.setObjectName(u"centering_validate_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/emblem-checked.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_validate_button.setIcon(icon1)

        self.gridLayout_3.addWidget(self.centering_validate_button, 0, 1, 1, 1)

        self.centering_volume_button = QToolButton(self.centering_widget)
        self.centering_volume_button.setObjectName(u"centering_volume_button")
        self.centering_volume_button.setCheckable(True)

        self.gridLayout_3.addWidget(self.centering_volume_button, 0, 0, 1, 1)

        self.centering_reason_label = KLabel(self.centering_widget)
        self.centering_reason_label.setObjectName(u"centering_reason_label")
        self.centering_reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_3.addWidget(self.centering_reason_label, 2, 1, 1, 1)

        self.centering_abort_button = QPushButton(self.centering_widget)
        self.centering_abort_button.setObjectName(u"centering_abort_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/emblem-error.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_abort_button.setIcon(icon2)

        self.gridLayout_3.addWidget(self.centering_abort_button, 0, 2, 1, 1)

        self.centering_spiral_search_button = QPushButton(self.centering_widget)
        self.centering_spiral_search_button.setObjectName(u"centering_spiral_search_button")
        icon3 = QIcon()
        icon3.addFile(u":/assets/icons/spiral-shape.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.centering_spiral_search_button.setIcon(icon3)

        self.gridLayout_3.addWidget(self.centering_spiral_search_button, 1, 1, 1, 1)

        self.centering_star_button = QPushButton(self.centering_widget)
        self.centering_star_button.setObjectName(u"centering_star_button")
        self.centering_star_button.setIcon(icon)

        self.gridLayout_3.addWidget(self.centering_star_button, 1, 2, 1, 1)


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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.keywords_button_widget.sizePolicy().hasHeightForWidth())
        self.keywords_button_widget.setSizePolicy(sizePolicy1)
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
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.keywords_widget.sizePolicy().hasHeightForWidth())
        self.keywords_widget.setSizePolicy(sizePolicy2)
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
        self.menubar.setGeometry(QRect(0, 0, 1534, 23))
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
        self.saturation_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Saturation {saturation:.0f} %", None))
        self.y_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Y", None))
        self.frame_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Frame", None))
        self.value_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Value", None))
        self.y_spinbox.setSuffix(QCoreApplication.translate("FITSViewerWindow", u" px", None))
        self.x_spinbox.setSuffix(QCoreApplication.translate("FITSViewerWindow", u" px", None))
        self.wcs_1_label.setText(QCoreApplication.translate("FITSViewerWindow", u"{ctype1}", None))
        self.x_label.setText(QCoreApplication.translate("FITSViewerWindow", u"X", None))
        self.wcs_2_label.setText(QCoreApplication.translate("FITSViewerWindow", u"{ctype2}", None))
        self.wcs_system_label.setText(QCoreApplication.translate("FITSViewerWindow", u"System", None))
        self.relative_coord_checkbox.setText(QCoreApplication.translate("FITSViewerWindow", u"Relative coordinates", None))
        self.timestamp_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Timestamp: {timestamp}", None))
        self.star_x_label.setText(QCoreApplication.translate("FITSViewerWindow", u"X: {x:.{axis_precision}f}{axis_unit}", None))
        self.star_y_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Y: {y:.{axis_precision}f}{axis_unit}", None))
        self.star_fwhm_label.setText(QCoreApplication.translate("FITSViewerWindow", u"FWHM: {fwhm:.{axis_precision}f}{axis_unit}", None))
        self.star_peak_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Peak: {peak:.{data_precision}f}{data_unit}", None))
        self.centering_timeout_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Time left: {timeout:.0f} s", None))
        self.centering_validate_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Validate manual centering", None))
        self.centering_volume_button.setText("")
        self.centering_reason_label.setText(QCoreApplication.translate("FITSViewerWindow", u"Reason: {reason}", None))
        self.centering_abort_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Abort", None))
        self.centering_spiral_search_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Spiral search", None))
        self.centering_star_button.setText(QCoreApplication.translate("FITSViewerWindow", u"Automatic star centering", None))
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

