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
    QLabel, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KImageViewer, KLabel, KScaledDoubleSpinbox)

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
        self.scale_layout = QGridLayout()
        self.scale_layout.setObjectName(u"scale_layout")
        self.saturation_label = KLabel(SlopesWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scale_layout.addWidget(self.saturation_label, 2, 0, 1, 3, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.min_spinbox = KScaledDoubleSpinbox(SlopesWidget)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setKeyboardTracking(False)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setMinimum(-99.000000000000000)
        self.min_spinbox.setMaximum(99.000000000000000)
        self.min_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.min_spinbox, 1, 0, 1, 1)

        self.max_spinbox = KScaledDoubleSpinbox(SlopesWidget)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setKeyboardTracking(False)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setMinimum(-99.000000000000000)
        self.max_spinbox.setMaximum(99.000000000000000)
        self.max_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.max_spinbox, 1, 2, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self.minmax_label = QLabel(SlopesWidget)
        self.minmax_label.setObjectName(u"minmax_label")

        self.scale_layout.addWidget(self.minmax_label, 1, 1, 1, 1)

        self.fullscale_button = QToolButton(SlopesWidget)
        self.fullscale_button.setObjectName(u"fullscale_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fullscale_button.sizePolicy().hasHeightForWidth())
        self.fullscale_button.setSizePolicy(sizePolicy)
        self.fullscale_button.setCheckable(True)

        self.scale_layout.addWidget(self.fullscale_button, 0, 2, 1, 1)

        self.autoscale_button = QToolButton(SlopesWidget)
        self.autoscale_button.setObjectName(u"autoscale_button")
        sizePolicy.setHeightForWidth(self.autoscale_button.sizePolicy().hasHeightForWidth())
        self.autoscale_button.setSizePolicy(sizePolicy)
        self.autoscale_button.setCheckable(True)
        self.autoscale_button.setChecked(True)

        self.scale_layout.addWidget(self.autoscale_button, 0, 0, 1, 1)

        self.scale_layout.setColumnStretch(0, 1)
        self.scale_layout.setColumnStretch(2, 1)

        self.side_layout.addLayout(self.scale_layout)

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
        self.minmax_label.setText(QCoreApplication.translate("SlopesWidget", u"\u2013", None))
        self.fullscale_button.setText(QCoreApplication.translate("SlopesWidget", u"Fullscale", None))
        self.autoscale_button.setText(QCoreApplication.translate("SlopesWidget", u"Autoscale", None))
        self.slope_x_avg_label.setText(QCoreApplication.translate("SlopesWidget", u"Average X: {slope_x_avg:.{precision}f}{unit}", None))
        self.slope_y_avg_label.setText(QCoreApplication.translate("SlopesWidget", u"Average Y: {slope_y_avg:.{precision}f}{unit}", None))
        self.residual_rms_label.setText(QCoreApplication.translate("SlopesWidget", u"Residual: {residual_rms:.{precision}f}{unit}", None))
    # retranslateUi

