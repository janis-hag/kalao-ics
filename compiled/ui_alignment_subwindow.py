# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alignment_subwindow.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QSizePolicy, QWidget)

from kalao.guis.utils.widgets import (KImageViewer, KLabel)

class Ui_AlignmentSubwindow(object):
    def setupUi(self, AlignmentSubwindow):
        if not AlignmentSubwindow.objectName():
            AlignmentSubwindow.setObjectName(u"AlignmentSubwindow")
        AlignmentSubwindow.resize(284, 240)
        self.gridLayout = QGridLayout(AlignmentSubwindow)
        self.gridLayout.setObjectName(u"gridLayout")
        self.view_3 = KImageViewer(AlignmentSubwindow)
        self.view_3.setObjectName(u"view_3")
        self.view_3.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view_3.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.view_3, 2, 0, 1, 1)

        self.label_3 = KLabel(AlignmentSubwindow)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.label_1 = KLabel(AlignmentSubwindow)
        self.label_1.setObjectName(u"label_1")
        self.label_1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_1, 1, 0, 1, 1)

        self.view_4 = KImageViewer(AlignmentSubwindow)
        self.view_4.setObjectName(u"view_4")
        self.view_4.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view_4.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.view_4, 2, 1, 1, 1)

        self.label_4 = KLabel(AlignmentSubwindow)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_4, 3, 1, 1, 1)

        self.view_1 = KImageViewer(AlignmentSubwindow)
        self.view_1.setObjectName(u"view_1")
        self.view_1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view_1.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.view_1, 0, 0, 1, 1)

        self.label_2 = KLabel(AlignmentSubwindow)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 1, 1, 1, 1)

        self.view_2 = KImageViewer(AlignmentSubwindow)
        self.view_2.setObjectName(u"view_2")
        self.view_2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view_2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.view_2, 0, 1, 1, 1)


        self.retranslateUi(AlignmentSubwindow)

        QMetaObject.connectSlotsByName(AlignmentSubwindow)
    # setupUi

    def retranslateUi(self, AlignmentSubwindow):
        AlignmentSubwindow.setWindowTitle(QCoreApplication.translate("AlignmentSubwindow", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("AlignmentSubwindow", u"{r:.3f}px @ {phi:.0f}\u00b0", None))
        self.label_1.setText(QCoreApplication.translate("AlignmentSubwindow", u"{r:.3f}px @ {phi:.0f}\u00b0", None))
        self.label_4.setText(QCoreApplication.translate("AlignmentSubwindow", u"{r:.3f}px @ {phi:.0f}\u00b0", None))
        self.label_2.setText(QCoreApplication.translate("AlignmentSubwindow", u"{r:.3f}px @ {phi:.0f}\u00b0", None))
    # retranslateUi

