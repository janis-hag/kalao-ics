# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'slopes.ui'
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

class Ui_SlopesWidget(object):
    def setupUi(self, SlopesWidget):
        if not SlopesWidget.objectName():
            SlopesWidget.setObjectName(u"SlopesWidget")
        SlopesWidget.resize(836, 494)
        self.gridLayout = QGridLayout(SlopesWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.title_label = QLabel(SlopesWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.minmax_widget = ImgMinMaxPart(SlopesWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(SlopesWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.slope_x_avg_label = KLabel(SlopesWidget)
        self.slope_x_avg_label.setObjectName(u"slope_x_avg_label")
        self.slope_x_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.slope_x_avg_label)

        self.slope_y_avg_label = KLabel(SlopesWidget)
        self.slope_y_avg_label.setObjectName(u"slope_y_avg_label")
        self.slope_y_avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.slope_y_avg_label)

        self.residual_rms_label = KLabel(SlopesWidget)
        self.residual_rms_label.setObjectName(u"residual_rms_label")
        self.residual_rms_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.residual_rms_label)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.slopes_view = KImageViewer(SlopesWidget)
        self.slopes_view.setObjectName(u"slopes_view")
        self.slopes_view.setEnabled(True)
        self.slopes_view.setFrameShape(QFrame.Shape.NoFrame)
        self.slopes_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.slopes_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.slopes_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.slopes_view, 1, 1, 1, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(SlopesWidget)

        QMetaObject.connectSlotsByName(SlopesWidget)
    # setupUi

    def retranslateUi(self, SlopesWidget):
        SlopesWidget.setWindowTitle(QCoreApplication.translate("SlopesWidget", u"Slopes - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("SlopesWidget", u"Slopes", None))
        self.saturation_label.setText(QCoreApplication.translate("SlopesWidget", u"Saturation {saturation:.0f} %", None))
        self.slope_x_avg_label.setText(QCoreApplication.translate("SlopesWidget", u"Average X: {slope_x_avg:.{precision}f}{unit}", None))
        self.slope_y_avg_label.setText(QCoreApplication.translate("SlopesWidget", u"Average Y: {slope_y_avg:.{precision}f}{unit}", None))
        self.residual_rms_label.setText(QCoreApplication.translate("SlopesWidget", u"Residual: {residual_rms:.{precision}f}{unit}", None))
    # retranslateUi

