# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'focus_sequence.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QMainWindow,
    QMenuBar, QSizePolicy, QStatusBar, QWidget)

from kalao.guis.utils.widgets import (KChartView, KLabel)

class Ui_FocusSequenceWindow(object):
    def setupUi(self, FocusSequenceWindow):
        if not FocusSequenceWindow.objectName():
            FocusSequenceWindow.setObjectName(u"FocusSequenceWindow")
        FocusSequenceWindow.resize(748, 418)
        self.centralwidget = QWidget(FocusSequenceWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.sequence_plot = KChartView(self.centralwidget)
        self.sequence_plot.setObjectName(u"sequence_plot")

        self.gridLayout.addWidget(self.sequence_plot, 1, 1, 1, 1)

        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 0, 1, 2)

        self.sequence_layout = QGridLayout()
        self.sequence_layout.setObjectName(u"sequence_layout")

        self.gridLayout.addLayout(self.sequence_layout, 1, 0, 2, 1)

        self.status_label = KLabel(self.centralwidget)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.status_label, 2, 1, 1, 1)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)
        FocusSequenceWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(FocusSequenceWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 748, 30))
        FocusSequenceWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(FocusSequenceWindow)
        self.statusbar.setObjectName(u"statusbar")
        FocusSequenceWindow.setStatusBar(self.statusbar)

        self.retranslateUi(FocusSequenceWindow)

        QMetaObject.connectSlotsByName(FocusSequenceWindow)
    # setupUi

    def retranslateUi(self, FocusSequenceWindow):
        FocusSequenceWindow.setWindowTitle(QCoreApplication.translate("FocusSequenceWindow", u"Focus - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("FocusSequenceWindow", u"Focus Sequence", None))
        self.status_label.setText(QCoreApplication.translate("FocusSequenceWindow", u"Status: {status}", None))
    # retranslateUi

