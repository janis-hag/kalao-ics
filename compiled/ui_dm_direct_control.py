# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dm_direct_control.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSlider,
    QVBoxLayout, QWidget)
from . import rc_assets

class Ui_DMDirectControlWindow(object):
    def setupUi(self, DMDirectControlWindow):
        if not DMDirectControlWindow.objectName():
            DMDirectControlWindow.setObjectName(u"DMDirectControlWindow")
        DMDirectControlWindow.resize(907, 710)
        self.centralwidget = QWidget(DMDirectControlWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(self.centralwidget)
        self.reset_button.setObjectName(u"reset_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/refreshstructure.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.reset_button.setIcon(icon)

        self.gridLayout.addWidget(self.reset_button, 3, 0, 1, 1)

        self.all_slider = QSlider(self.centralwidget)
        self.all_slider.setObjectName(u"all_slider")
        self.all_slider.setMinimum(-175)
        self.all_slider.setMaximum(175)
        self.all_slider.setSingleStep(1)
        self.all_slider.setPageStep(25)
        self.all_slider.setOrientation(Qt.Orientation.Horizontal)
        self.all_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.all_slider.setTickInterval(25)

        self.gridLayout.addWidget(self.all_slider, 2, 0, 1, 1)

        self.actuator_grid = QGridLayout()
        self.actuator_grid.setSpacing(0)
        self.actuator_grid.setObjectName(u"actuator_grid")

        self.gridLayout.addLayout(self.actuator_grid, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.load_button = QPushButton(self.centralwidget)
        self.load_button.setObjectName(u"load_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/document-open.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.load_button.setIcon(icon1)

        self.horizontalLayout.addWidget(self.load_button)

        self.save_button = QPushButton(self.centralwidget)
        self.save_button.setObjectName(u"save_button")
        icon2 = QIcon()
        icon2.addFile(u":/assets/icons/document-save.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.save_button.setIcon(icon2)

        self.horizontalLayout.addWidget(self.save_button)


        self.gridLayout.addLayout(self.horizontalLayout, 4, 0, 1, 1)

        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 0, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.zernike_groupbox = QGroupBox(self.centralwidget)
        self.zernike_groupbox.setObjectName(u"zernike_groupbox")
        self.formLayout_3 = QFormLayout(self.zernike_groupbox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout.addWidget(self.zernike_groupbox)

        self.checkerboard_groupbox = QGroupBox(self.centralwidget)
        self.checkerboard_groupbox.setObjectName(u"checkerboard_groupbox")
        self.formLayout = QFormLayout(self.checkerboard_groupbox)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.checkerboard_amplitude_label = QLabel(self.checkerboard_groupbox)
        self.checkerboard_amplitude_label.setObjectName(u"checkerboard_amplitude_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.checkerboard_amplitude_label)

        self.checkerboard_amplitude_spinbox = QDoubleSpinBox(self.checkerboard_groupbox)
        self.checkerboard_amplitude_spinbox.setObjectName(u"checkerboard_amplitude_spinbox")
        self.checkerboard_amplitude_spinbox.setKeyboardTracking(False)
        self.checkerboard_amplitude_spinbox.setMinimum(-1.750000000000000)
        self.checkerboard_amplitude_spinbox.setMaximum(1.750000000000000)
        self.checkerboard_amplitude_spinbox.setSingleStep(0.050000000000000)

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.checkerboard_amplitude_spinbox)

        self.checkerboard_period_label = QLabel(self.checkerboard_groupbox)
        self.checkerboard_period_label.setObjectName(u"checkerboard_period_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.checkerboard_period_label)

        self.checkerboard_period_spinbox = QDoubleSpinBox(self.checkerboard_groupbox)
        self.checkerboard_period_spinbox.setObjectName(u"checkerboard_period_spinbox")
        self.checkerboard_period_spinbox.setKeyboardTracking(False)
        self.checkerboard_period_spinbox.setDecimals(0)
        self.checkerboard_period_spinbox.setMinimum(2.000000000000000)
        self.checkerboard_period_spinbox.setMaximum(12.000000000000000)
        self.checkerboard_period_spinbox.setSingleStep(2.000000000000000)

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.checkerboard_period_spinbox)


        self.verticalLayout.addWidget(self.checkerboard_groupbox)

        self.grating_groupbox = QGroupBox(self.centralwidget)
        self.grating_groupbox.setObjectName(u"grating_groupbox")
        self.formLayout_4 = QFormLayout(self.grating_groupbox)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setLabelAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.grating_amplitude_label = QLabel(self.grating_groupbox)
        self.grating_amplitude_label.setObjectName(u"grating_amplitude_label")

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.grating_amplitude_label)

        self.grating_amplitude_spinbox = QDoubleSpinBox(self.grating_groupbox)
        self.grating_amplitude_spinbox.setObjectName(u"grating_amplitude_spinbox")
        self.grating_amplitude_spinbox.setKeyboardTracking(False)
        self.grating_amplitude_spinbox.setMinimum(-1.750000000000000)
        self.grating_amplitude_spinbox.setMaximum(1.750000000000000)
        self.grating_amplitude_spinbox.setSingleStep(0.050000000000000)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.grating_amplitude_spinbox)

        self.grating_period_label = QLabel(self.grating_groupbox)
        self.grating_period_label.setObjectName(u"grating_period_label")

        self.formLayout_4.setWidget(1, QFormLayout.LabelRole, self.grating_period_label)

        self.grating_angle_label = QLabel(self.grating_groupbox)
        self.grating_angle_label.setObjectName(u"grating_angle_label")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.grating_angle_label)

        self.grating_angle_spinbox = QDoubleSpinBox(self.grating_groupbox)
        self.grating_angle_spinbox.setObjectName(u"grating_angle_spinbox")
        self.grating_angle_spinbox.setKeyboardTracking(False)
        self.grating_angle_spinbox.setDecimals(0)
        self.grating_angle_spinbox.setMaximum(360.000000000000000)
        self.grating_angle_spinbox.setSingleStep(15.000000000000000)

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.grating_angle_spinbox)

        self.grating_period_spinbox = QDoubleSpinBox(self.grating_groupbox)
        self.grating_period_spinbox.setObjectName(u"grating_period_spinbox")
        self.grating_period_spinbox.setKeyboardTracking(False)
        self.grating_period_spinbox.setMinimum(2.000000000000000)
        self.grating_period_spinbox.setMaximum(24.000000000000000)
        self.grating_period_spinbox.setValue(2.000000000000000)

        self.formLayout_4.setWidget(1, QFormLayout.FieldRole, self.grating_period_spinbox)


        self.verticalLayout.addWidget(self.grating_groupbox)


        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 4, 1)

        self.gridLayout.setRowStretch(1, 1)
        DMDirectControlWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(DMDirectControlWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 907, 30))
        DMDirectControlWindow.setMenuBar(self.menubar)

        self.retranslateUi(DMDirectControlWindow)

        QMetaObject.connectSlotsByName(DMDirectControlWindow)
    # setupUi

    def retranslateUi(self, DMDirectControlWindow):
        DMDirectControlWindow.setWindowTitle(QCoreApplication.translate("DMDirectControlWindow", u"DM Direct Control - KalAO", None))
        self.reset_button.setText(QCoreApplication.translate("DMDirectControlWindow", u"Reset", None))
        self.load_button.setText(QCoreApplication.translate("DMDirectControlWindow", u"Load from ...", None))
        self.save_button.setText(QCoreApplication.translate("DMDirectControlWindow", u"Save to ...", None))
        self.title_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Deformable Mirror Direct Control", None))
        self.zernike_groupbox.setTitle(QCoreApplication.translate("DMDirectControlWindow", u"Zernike (RMS)", None))
        self.checkerboard_groupbox.setTitle(QCoreApplication.translate("DMDirectControlWindow", u"Checkerboard", None))
        self.checkerboard_amplitude_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Amplitude", None))
        self.checkerboard_amplitude_spinbox.setSuffix(QCoreApplication.translate("DMDirectControlWindow", u" \u00b5m", None))
        self.checkerboard_period_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Period", None))
        self.checkerboard_period_spinbox.setSuffix(QCoreApplication.translate("DMDirectControlWindow", u" px", None))
        self.grating_groupbox.setTitle(QCoreApplication.translate("DMDirectControlWindow", u"Grating", None))
        self.grating_amplitude_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Amplitude", None))
        self.grating_amplitude_spinbox.setSuffix(QCoreApplication.translate("DMDirectControlWindow", u" \u00b5m", None))
        self.grating_period_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Period", None))
        self.grating_angle_label.setText(QCoreApplication.translate("DMDirectControlWindow", u"Angle", None))
        self.grating_angle_spinbox.setSuffix(QCoreApplication.translate("DMDirectControlWindow", u"\u00b0", None))
        self.grating_period_spinbox.setSuffix(QCoreApplication.translate("DMDirectControlWindow", u" px", None))
    # retranslateUi

