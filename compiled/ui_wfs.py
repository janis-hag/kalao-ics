# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wfs.ui'
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
    QLabel, QSizePolicy, QSpacerItem, QWidget)

from kalao.guis.utils.parts import ImgMinMaxPart
from kalao.guis.utils.widgets import (KImageViewer, KLabel)

class Ui_WFSWidget(object):
    def setupUi(self, WFSWidget):
        if not WFSWidget.objectName():
            WFSWidget.setObjectName(u"WFSWidget")
        WFSWidget.resize(889, 475)
        self.gridLayout = QGridLayout(WFSWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.title_label = QLabel(WFSWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.wfs_view = KImageViewer(WFSWidget)
        self.wfs_view.setObjectName(u"wfs_view")
        self.wfs_view.setEnabled(True)
        self.wfs_view.setFrameShape(QFrame.Shape.NoFrame)
        self.wfs_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.wfs_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.wfs_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.wfs_view, 1, 1, 1, 1)

        self.side_layout = QGridLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.label = QLabel(WFSWidget)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.side_layout.addWidget(self.label, 3, 0, 1, 1)

        self.minmax_widget = ImgMinMaxPart(WFSWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget, 0, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer_2, 2, 0, 1, 2)

        self.saturation_label = KLabel(WFSWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label, 1, 0, 1, 1)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(WFSWidget)

        QMetaObject.connectSlotsByName(WFSWidget)
    # setupUi

    def retranslateUi(self, WFSWidget):
        WFSWidget.setWindowTitle(QCoreApplication.translate("WFSWidget", u"Wavefront Sensor - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("WFSWidget", u"Wavefront Sensor", None))
        self.label.setText(QCoreApplication.translate("WFSWidget", u"<a href=\"https://gitlab.unige.ch/kalao/kalao-ics/-/wikis/Technical/WFS,-DM-and-telescope-pupil\">More details about WFS, DM and telescope pupil here.</a>", None))
        self.saturation_label.setText(QCoreApplication.translate("WFSWidget", u"Saturation {saturation:.0f} %", None))
    # retranslateUi

