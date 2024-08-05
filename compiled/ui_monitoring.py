# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monitoring.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout,
    QWidget)

from kalao.guis.utils.widgets import KLabel

class Ui_MonitoringWidget(object):
    def setupUi(self, MonitoringWidget):
        if not MonitoringWidget.objectName():
            MonitoringWidget.setObjectName(u"MonitoringWidget")
        MonitoringWidget.resize(934, 569)
        self.verticalLayout = QVBoxLayout(MonitoringWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.last_update_label = KLabel(MonitoringWidget)
        self.last_update_label.setObjectName(u"last_update_label")
        font = QFont()
        font.setBold(True)
        self.last_update_label.setFont(font)
        self.last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.last_update_label)

        self.data_layout = QHBoxLayout()
        self.data_layout.setObjectName(u"data_layout")

        self.verticalLayout.addLayout(self.data_layout)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(MonitoringWidget)

        QMetaObject.connectSlotsByName(MonitoringWidget)
    # setupUi

    def retranslateUi(self, MonitoringWidget):
        MonitoringWidget.setWindowTitle(QCoreApplication.translate("MonitoringWidget", u"Monitoring - KalAO", None))
        self.last_update_label.setText(QCoreApplication.translate("MonitoringWidget", u"Last update: {last_update}", None))
    # retranslateUi

