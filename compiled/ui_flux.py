# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'flux.ui'
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
from kalao.guis.utils.widgets import (KImageViewer, KLabel)

class Ui_FluxWidget(object):
    def setupUi(self, FluxWidget):
        if not FluxWidget.objectName():
            FluxWidget.setObjectName(u"FluxWidget")
        FluxWidget.resize(837, 497)
        self.gridLayout = QGridLayout(FluxWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.title_label = QLabel(FluxWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.flux_view = KImageViewer(FluxWidget)
        self.flux_view.setObjectName(u"flux_view")
        self.flux_view.setEnabled(True)
        self.flux_view.setFrameShape(QFrame.Shape.NoFrame)
        self.flux_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.flux_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.flux_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.flux_view, 1, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.minmax_widget = ImgMinMaxPart(FluxWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(FluxWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.flux_avg_label = KLabel(FluxWidget)
        self.flux_avg_label.setObjectName(u"flux_avg_label")
        self.flux_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.flux_avg_label)

        self.flux_brightest_label = KLabel(FluxWidget)
        self.flux_brightest_label.setObjectName(u"flux_brightest_label")
        self.flux_brightest_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.flux_brightest_label)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(FluxWidget)

        QMetaObject.connectSlotsByName(FluxWidget)
    # setupUi

    def retranslateUi(self, FluxWidget):
        FluxWidget.setWindowTitle(QCoreApplication.translate("FluxWidget", u"Flux - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("FluxWidget", u"Flux", None))
        self.saturation_label.setText(QCoreApplication.translate("FluxWidget", u"Saturation {saturation:.0f} %", None))
        self.flux_avg_label.setText(QCoreApplication.translate("FluxWidget", u"Average flux: {flux_avg:.0f}{unit}", None))
        self.flux_brightest_label.setText(QCoreApplication.translate("FluxWidget", u"Brightest Flux: {flux_brightest:.0f}{unit}", None))
    # retranslateUi

