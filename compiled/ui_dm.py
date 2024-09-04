# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dm.ui'
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

class Ui_DMWidget(object):
    def setupUi(self, DMWidget):
        if not DMWidget.objectName():
            DMWidget.setObjectName(u"DMWidget")
        DMWidget.resize(827, 495)
        self.gridLayout = QGridLayout(DMWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.title_label = QLabel(DMWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.minmax_widget = ImgMinMaxPart(DMWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(DMWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.stroke_raw_label = KLabel(DMWidget)
        self.stroke_raw_label.setObjectName(u"stroke_raw_label")
        self.stroke_raw_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.stroke_raw_label)

        self.stroke_effective_label = KLabel(DMWidget)
        self.stroke_effective_label.setObjectName(u"stroke_effective_label")
        self.stroke_effective_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.stroke_effective_label)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.dm_view = KImageViewer(DMWidget)
        self.dm_view.setObjectName(u"dm_view")
        self.dm_view.setEnabled(True)
        self.dm_view.setFrameShape(QFrame.Shape.NoFrame)
        self.dm_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.dm_view, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(DMWidget)

        QMetaObject.connectSlotsByName(DMWidget)
    # setupUi

    def retranslateUi(self, DMWidget):
        DMWidget.setWindowTitle(QCoreApplication.translate("DMWidget", u"Deformable Mirror - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("DMWidget", u"Deformable Mirror", None))
        self.saturation_label.setText(QCoreApplication.translate("DMWidget", u"Saturation {saturation:.0f} %", None))
        self.stroke_raw_label.setText(QCoreApplication.translate("DMWidget", u"Stroke (raw): {stroke_raw:.2f}{unit}", None))
        self.stroke_effective_label.setText(QCoreApplication.translate("DMWidget", u"Stroke (actual): {stroke_effective:.2f}{unit}", None))
    # retranslateUi

