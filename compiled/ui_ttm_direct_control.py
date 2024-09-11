# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ttm_direct_control.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QHBoxLayout, QLabel,
    QMainWindow, QMenuBar, QSizePolicy, QSlider,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_TTMDirectControlWindow(object):
    def setupUi(self, TTMDirectControlWindow):
        if not TTMDirectControlWindow.objectName():
            TTMDirectControlWindow.setObjectName(u"TTMDirectControlWindow")
        TTMDirectControlWindow.resize(846, 164)
        self.centralwidget = QWidget(TTMDirectControlWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.title_label)

        self.tip_slider = QSlider(self.centralwidget)
        self.tip_slider.setObjectName(u"tip_slider")
        self.tip_slider.setMinimum(-2500)
        self.tip_slider.setMaximum(2500)
        self.tip_slider.setOrientation(Qt.Orientation.Horizontal)
        self.tip_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.tip_slider.setTickInterval(250)

        self.verticalLayout.addWidget(self.tip_slider)

        self.tilt_slider = QSlider(self.centralwidget)
        self.tilt_slider.setObjectName(u"tilt_slider")
        self.tilt_slider.setMinimum(-2500)
        self.tilt_slider.setMaximum(2500)
        self.tilt_slider.setSingleStep(100)
        self.tilt_slider.setPageStep(500)
        self.tilt_slider.setOrientation(Qt.Orientation.Horizontal)
        self.tilt_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.tilt_slider.setTickInterval(250)

        self.verticalLayout.addWidget(self.tilt_slider)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tip_label = QLabel(self.centralwidget)
        self.tip_label.setObjectName(u"tip_label")
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.tip_label)

        self.tip_spinbox = QDoubleSpinBox(self.centralwidget)
        self.tip_spinbox.setObjectName(u"tip_spinbox")
        self.tip_spinbox.setKeyboardTracking(False)
        self.tip_spinbox.setMinimum(-25.000000000000000)
        self.tip_spinbox.setMaximum(2.500000000000000)
        self.tip_spinbox.setSingleStep(0.050000000000000)

        self.horizontalLayout.addWidget(self.tip_spinbox)

        self.tilt_label = QLabel(self.centralwidget)
        self.tilt_label.setObjectName(u"tilt_label")
        self.tilt_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.tilt_label)

        self.tilt_spinbox = QDoubleSpinBox(self.centralwidget)
        self.tilt_spinbox.setObjectName(u"tilt_spinbox")
        self.tilt_spinbox.setKeyboardTracking(False)
        self.tilt_spinbox.setMinimum(-25.000000000000000)
        self.tilt_spinbox.setMaximum(2.500000000000000)
        self.tilt_spinbox.setSingleStep(0.050000000000000)

        self.horizontalLayout.addWidget(self.tilt_spinbox)


        self.verticalLayout.addLayout(self.horizontalLayout)

        TTMDirectControlWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(TTMDirectControlWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 846, 23))
        TTMDirectControlWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(TTMDirectControlWindow)
        self.statusbar.setObjectName(u"statusbar")
        TTMDirectControlWindow.setStatusBar(self.statusbar)

        self.retranslateUi(TTMDirectControlWindow)

        QMetaObject.connectSlotsByName(TTMDirectControlWindow)
    # setupUi

    def retranslateUi(self, TTMDirectControlWindow):
        TTMDirectControlWindow.setWindowTitle(QCoreApplication.translate("TTMDirectControlWindow", u"TTM Direct Control - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("TTMDirectControlWindow", u"TTM Direct Control", None))
        self.tip_label.setText(QCoreApplication.translate("TTMDirectControlWindow", u"Tip", None))
        self.tip_spinbox.setSuffix(QCoreApplication.translate("TTMDirectControlWindow", u" mrad", None))
        self.tilt_label.setText(QCoreApplication.translate("TTMDirectControlWindow", u"Tilt", None))
        self.tilt_spinbox.setSuffix(QCoreApplication.translate("TTMDirectControlWindow", u" mrad", None))
    # retranslateUi

