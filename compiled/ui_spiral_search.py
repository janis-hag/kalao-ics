# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'spiral_search.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QGraphicsView, QGridLayout,
    QLabel, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSpinBox, QStatusBar, QWidget)

from kalao.guis.utils.widgets import KLabel
from . import rc_assets

class Ui_SpiralSearchWindow(object):
    def setupUi(self, SpiralSearchWindow):
        if not SpiralSearchWindow.objectName():
            SpiralSearchWindow.setObjectName(u"SpiralSearchWindow")
        SpiralSearchWindow.resize(800, 600)
        self.centralwidget = QWidget(SpiralSearchWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.spiral_search_view = QGraphicsView(self.centralwidget)
        self.spiral_search_view.setObjectName(u"spiral_search_view")

        self.gridLayout.addWidget(self.spiral_search_view, 0, 0, 1, 3)

        self.overlap_label = QLabel(self.centralwidget)
        self.overlap_label.setObjectName(u"overlap_label")
        self.overlap_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.overlap_label, 2, 1, 1, 1)

        self.area_label = KLabel(self.centralwidget)
        self.area_label.setObjectName(u"area_label")
        self.area_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.area_label, 1, 0, 1, 1)

        self.radius_spinbox = QSpinBox(self.centralwidget)
        self.radius_spinbox.setObjectName(u"radius_spinbox")
        self.radius_spinbox.setReadOnly(True)
        self.radius_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.radius_spinbox.setMinimum(1)

        self.gridLayout.addWidget(self.radius_spinbox, 1, 2, 1, 1)

        self.star_label = KLabel(self.centralwidget)
        self.star_label.setObjectName(u"star_label")
        self.star_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.star_label, 2, 0, 1, 1)

        self.overlap_spinbox = QSpinBox(self.centralwidget)
        self.overlap_spinbox.setObjectName(u"overlap_spinbox")
        self.overlap_spinbox.setReadOnly(True)
        self.overlap_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.overlap_spinbox.setMinimum(0)
        self.overlap_spinbox.setMaximum(50)
        self.overlap_spinbox.setSingleStep(5)
        self.overlap_spinbox.setValue(15)

        self.gridLayout.addWidget(self.overlap_spinbox, 2, 2, 1, 1)

        self.radius_label = QLabel(self.centralwidget)
        self.radius_label.setObjectName(u"radius_label")
        self.radius_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.radius_label, 1, 1, 1, 1)

        self.abort_button = QPushButton(self.centralwidget)
        self.abort_button.setObjectName(u"abort_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/emblem-error.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.abort_button.setIcon(icon)

        self.gridLayout.addWidget(self.abort_button, 3, 0, 1, 3)

        self.gridLayout.setColumnStretch(0, 1)
        SpiralSearchWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(SpiralSearchWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 23))
        SpiralSearchWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(SpiralSearchWindow)
        self.statusbar.setObjectName(u"statusbar")
        SpiralSearchWindow.setStatusBar(self.statusbar)

        self.retranslateUi(SpiralSearchWindow)

        QMetaObject.connectSlotsByName(SpiralSearchWindow)
    # setupUi

    def retranslateUi(self, SpiralSearchWindow):
        SpiralSearchWindow.setWindowTitle(QCoreApplication.translate("SpiralSearchWindow", u"Spiral Search - KalAO", None))
        self.overlap_label.setText(QCoreApplication.translate("SpiralSearchWindow", u"Overlap", None))
        self.area_label.setText(QCoreApplication.translate("SpiralSearchWindow", u"Displayed area: {x} x {y}", None))
        self.radius_spinbox.setSuffix(QCoreApplication.translate("SpiralSearchWindow", u" frames", None))
        self.star_label.setText(QCoreApplication.translate("SpiralSearchWindow", u"Star position: {text}", None))
        self.overlap_spinbox.setSuffix(QCoreApplication.translate("SpiralSearchWindow", u" %", None))
        self.radius_label.setText(QCoreApplication.translate("SpiralSearchWindow", u"Radius", None))
        self.abort_button.setText(QCoreApplication.translate("SpiralSearchWindow", u"Abort", None))
    # retranslateUi

