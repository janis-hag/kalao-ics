# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'camera.ui'
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
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from kalao.guis.utils.parts import ImgMinMaxPart
from kalao.guis.utils.widgets import (KImageViewer, KLabel)
from . import rc_assets

class Ui_CameraWidget(object):
    def setupUi(self, CameraWidget):
        if not CameraWidget.objectName():
            CameraWidget.setObjectName(u"CameraWidget")
        CameraWidget.resize(823, 494)
        self.gridLayout = QGridLayout(CameraWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.title_label = QLabel(CameraWidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.title_label, 0, 1, 1, 1)

        self.camera_view = KImageViewer(CameraWidget)
        self.camera_view.setObjectName(u"camera_view")
        self.camera_view.setEnabled(True)
        self.camera_view.setFrameShape(QFrame.Shape.NoFrame)
        self.camera_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.camera_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.camera_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.camera_view, 1, 1, 1, 1)

        self.side_layout = QVBoxLayout()
        self.side_layout.setObjectName(u"side_layout")
        self.minmax_widget = ImgMinMaxPart(CameraWidget)
        self.minmax_widget.setObjectName(u"minmax_widget")

        self.side_layout.addWidget(self.minmax_widget)

        self.saturation_label = KLabel(CameraWidget)
        self.saturation_label.setObjectName(u"saturation_label")
        self.saturation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.saturation_label)

        self.linearity_label = QLabel(CameraWidget)
        self.linearity_label.setObjectName(u"linearity_label")
        self.linearity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.linearity_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.side_layout.addItem(self.verticalSpacer)

        self.timestamp_label = KLabel(CameraWidget)
        self.timestamp_label.setObjectName(u"timestamp_label")
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.side_layout.addWidget(self.timestamp_label)

        self.fits_viewer_button = QPushButton(CameraWidget)
        self.fits_viewer_button.setObjectName(u"fits_viewer_button")
        icon = QIcon()
        icon.addFile(u":/assets/icons/search.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.fits_viewer_button.setIcon(icon)

        self.side_layout.addWidget(self.fits_viewer_button)

        self.open_button = QPushButton(CameraWidget)
        self.open_button.setObjectName(u"open_button")
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/document-open.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.open_button.setIcon(icon1)

        self.side_layout.addWidget(self.open_button)


        self.gridLayout.addLayout(self.side_layout, 0, 0, 2, 1)

        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(CameraWidget)

        QMetaObject.connectSlotsByName(CameraWidget)
    # setupUi

    def retranslateUi(self, CameraWidget):
        CameraWidget.setWindowTitle(QCoreApplication.translate("CameraWidget", u"Science Camera - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("CameraWidget", u"Science Camera", None))
        self.saturation_label.setText(QCoreApplication.translate("CameraWidget", u"Saturation {saturation:.0f} %", None))
        self.linearity_label.setText(QCoreApplication.translate("CameraWidget", u"Inside of linear range", None))
        self.timestamp_label.setText(QCoreApplication.translate("CameraWidget", u"Timestamp: {timestamp}", None))
        self.fits_viewer_button.setText(QCoreApplication.translate("CameraWidget", u"Open detailed view ...", None))
        self.open_button.setText(QCoreApplication.translate("CameraWidget", u"Open a file ...", None))
    # retranslateUi

