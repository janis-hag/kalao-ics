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
    QLabel, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KImageViewer, KLabel, KScaledDoubleSpinbox)

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
        self.scale_layout = QGridLayout()
        self.scale_layout.setObjectName(u"scale_layout")
        self.saturation_label = KLabel(DMWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scale_layout.addWidget(self.saturation_label, 2, 0, 1, 3, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.min_spinbox = KScaledDoubleSpinbox(DMWidget)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setKeyboardTracking(False)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setMinimum(-99.000000000000000)
        self.min_spinbox.setMaximum(99.000000000000000)
        self.min_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.min_spinbox, 1, 0, 1, 1)

        self.max_spinbox = KScaledDoubleSpinbox(DMWidget)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setKeyboardTracking(False)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setMinimum(-99.000000000000000)
        self.max_spinbox.setMaximum(99.000000000000000)
        self.max_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.max_spinbox, 1, 2, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self.minmax_label = QLabel(DMWidget)
        self.minmax_label.setObjectName(u"minmax_label")

        self.scale_layout.addWidget(self.minmax_label, 1, 1, 1, 1)

        self.fullscale_button = QToolButton(DMWidget)
        self.fullscale_button.setObjectName(u"fullscale_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fullscale_button.sizePolicy().hasHeightForWidth())
        self.fullscale_button.setSizePolicy(sizePolicy)
        self.fullscale_button.setCheckable(True)

        self.scale_layout.addWidget(self.fullscale_button, 0, 2, 1, 1)

        self.autoscale_button = QToolButton(DMWidget)
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
        self.minmax_label.setText(QCoreApplication.translate("DMWidget", u"\u2013", None))
        self.fullscale_button.setText(QCoreApplication.translate("DMWidget", u"Fullscale", None))
        self.autoscale_button.setText(QCoreApplication.translate("DMWidget", u"Autoscale", None))
        self.stroke_raw_label.setText(QCoreApplication.translate("DMWidget", u"Stroke (raw): {stroke_raw:.2f}{unit}", None))
        self.stroke_effective_label.setText(QCoreApplication.translate("DMWidget", u"Stroke (actual): {stroke_effective:.2f}{unit}", None))
    # retranslateUi

