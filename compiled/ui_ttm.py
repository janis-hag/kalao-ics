# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ttm.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QFrame, QGridLayout,
    QLabel, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

from kalao.guis.utils.parts import ImgMinMaxPart
from kalao.guis.utils.widgets import (KChartView, KLabel)

class Ui_TTMWidget(object):
    def setupUi(self, TTMWidget):
        if not TTMWidget.objectName():
            TTMWidget.setObjectName(u"TTMWidget")
        TTMWidget.resize(834, 497)
        self.gridLayout = QGridLayout(TTMWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.minmax_widget = ImgMinMaxPart(TTMWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(TTMWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer_2)

        self.tip_label = KLabel(TTMWidget)
        self.tip_label.setObjectName(u"tip_label")
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.tip_label)

        self.tilt_label = KLabel(TTMWidget)
        self.tilt_label.setObjectName(u"tilt_label")
        self.tilt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.tilt_label)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.title_label = QLabel(TTMWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.tiptilt_plot = KChartView(TTMWidget)
        self.tiptilt_plot.setObjectName(u"tiptilt_plot")
        self.tiptilt_plot.setEnabled(True)
        self.tiptilt_plot.setFrameShape(QFrame.Shape.NoFrame)
        self.tiptilt_plot.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tiptilt_plot.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tiptilt_plot.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.tiptilt_plot, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(TTMWidget)

        QMetaObject.connectSlotsByName(TTMWidget)
    # setupUi

    def retranslateUi(self, TTMWidget):
        TTMWidget.setWindowTitle(QCoreApplication.translate("TTMWidget", u"Tip-Tilt Mirror - KalAO", None))
        self.saturation_label.setText(QCoreApplication.translate("TTMWidget", u"Saturation {saturation:.0f} %", None))
        self.tip_label.setText(QCoreApplication.translate("TTMWidget", u"Tip: {tip:.3f}{unit}", None))
        self.tilt_label.setText(QCoreApplication.translate("TTMWidget", u"Tilt: {tilt:.3f}{unit}", None))
        self.title_label.setText(QCoreApplication.translate("TTMWidget", u"Tip-Tilt Mirror", None))
    # retranslateUi

