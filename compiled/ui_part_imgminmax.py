# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'part_imgminmax.ui'
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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QGridLayout, QLabel,
    QSizePolicy, QToolButton, QWidget)

class Ui_ImgMinMaxPart(object):
    def setupUi(self, ImgMinMaxPart):
        if not ImgMinMaxPart.objectName():
            ImgMinMaxPart.setObjectName(u"ImgMinMaxPart")
        ImgMinMaxPart.resize(173, 57)
        self.gridLayout = QGridLayout(ImgMinMaxPart)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.max_spinbox = QDoubleSpinBox(ImgMinMaxPart)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setKeyboardTracking(False)

        self.gridLayout.addWidget(self.max_spinbox, 1, 2, 1, 1)

        self.minmax_label = QLabel(ImgMinMaxPart)
        self.minmax_label.setObjectName(u"minmax_label")

        self.gridLayout.addWidget(self.minmax_label, 1, 1, 1, 1)

        self.autoscale_button = QToolButton(ImgMinMaxPart)
        self.autoscale_button.setObjectName(u"autoscale_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autoscale_button.sizePolicy().hasHeightForWidth())
        self.autoscale_button.setSizePolicy(sizePolicy)
        self.autoscale_button.setCheckable(True)
        self.autoscale_button.setChecked(True)

        self.gridLayout.addWidget(self.autoscale_button, 0, 0, 1, 1)

        self.fullscale_button = QToolButton(ImgMinMaxPart)
        self.fullscale_button.setObjectName(u"fullscale_button")
        sizePolicy.setHeightForWidth(self.fullscale_button.sizePolicy().hasHeightForWidth())
        self.fullscale_button.setSizePolicy(sizePolicy)
        self.fullscale_button.setCheckable(True)

        self.gridLayout.addWidget(self.fullscale_button, 0, 2, 1, 1)

        self.min_spinbox = QDoubleSpinBox(ImgMinMaxPart)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setKeyboardTracking(False)

        self.gridLayout.addWidget(self.min_spinbox, 1, 0, 1, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(2, 1)

        self.retranslateUi(ImgMinMaxPart)

        QMetaObject.connectSlotsByName(ImgMinMaxPart)
    # setupUi

    def retranslateUi(self, ImgMinMaxPart):
        ImgMinMaxPart.setWindowTitle(QCoreApplication.translate("ImgMinMaxPart", u"ImgMinMaxPart", None))
        self.minmax_label.setText(QCoreApplication.translate("ImgMinMaxPart", u"\u2013", None))
        self.autoscale_button.setText(QCoreApplication.translate("ImgMinMaxPart", u"Autoscale", None))
        self.fullscale_button.setText(QCoreApplication.translate("ImgMinMaxPart", u"Fullscale", None))
    # retranslateUi

