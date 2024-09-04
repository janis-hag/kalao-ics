# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'help.ui'
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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QTextBrowser, QVBoxLayout,
    QWidget)

from kalao.guis.utils.parts import FindPart

class Ui_HelpWidget(object):
    def setupUi(self, HelpWidget):
        if not HelpWidget.objectName():
            HelpWidget.setObjectName(u"HelpWidget")
        HelpWidget.resize(886, 725)
        self.verticalLayout = QVBoxLayout(HelpWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.help_textedit = QTextBrowser(HelpWidget)
        self.help_textedit.setObjectName(u"help_textedit")
        self.help_textedit.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.help_textedit)

        self.find_widget = FindPart(HelpWidget)
        self.find_widget.setObjectName(u"find_widget")

        self.verticalLayout.addWidget(self.find_widget)


        self.retranslateUi(HelpWidget)

        QMetaObject.connectSlotsByName(HelpWidget)
    # setupUi

    def retranslateUi(self, HelpWidget):
        HelpWidget.setWindowTitle(QCoreApplication.translate("HelpWidget", u"Help - KalAO", None))
    # retranslateUi

