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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLineEdit,
    QSizePolicy, QTextBrowser, QToolButton, QVBoxLayout,
    QWidget)

class Ui_HelpWidget(object):
    def setupUi(self, HelpWidget):
        if not HelpWidget.objectName():
            HelpWidget.setObjectName(u"HelpWidget")
        HelpWidget.resize(886, 640)
        self.verticalLayout = QVBoxLayout(HelpWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.textedit = QTextBrowser(HelpWidget)
        self.textedit.setObjectName(u"textedit")
        self.textedit.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.textedit)

        self.searchlayout = QHBoxLayout()
        self.searchlayout.setObjectName(u"searchlayout")
        self.search_lineedit = QLineEdit(HelpWidget)
        self.search_lineedit.setObjectName(u"search_lineedit")
        self.search_lineedit.setClearButtonEnabled(True)

        self.searchlayout.addWidget(self.search_lineedit)

        self.next_button = QToolButton(HelpWidget)
        self.next_button.setObjectName(u"next_button")
        self.next_button.setEnabled(False)
        self.next_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.next_button.setArrowType(Qt.ArrowType.DownArrow)

        self.searchlayout.addWidget(self.next_button)

        self.previous_button = QToolButton(HelpWidget)
        self.previous_button.setObjectName(u"previous_button")
        self.previous_button.setEnabled(False)
        self.previous_button.setArrowType(Qt.ArrowType.UpArrow)

        self.searchlayout.addWidget(self.previous_button)

        self.casesensitive_checkbox = QCheckBox(HelpWidget)
        self.casesensitive_checkbox.setObjectName(u"casesensitive_checkbox")

        self.searchlayout.addWidget(self.casesensitive_checkbox)

        self.wholewords_checkbox = QCheckBox(HelpWidget)
        self.wholewords_checkbox.setObjectName(u"wholewords_checkbox")

        self.searchlayout.addWidget(self.wholewords_checkbox)


        self.verticalLayout.addLayout(self.searchlayout)


        self.retranslateUi(HelpWidget)

        QMetaObject.connectSlotsByName(HelpWidget)
    # setupUi

    def retranslateUi(self, HelpWidget):
        HelpWidget.setWindowTitle(QCoreApplication.translate("HelpWidget", u"Help - KalAO", None))
        self.search_lineedit.setPlaceholderText(QCoreApplication.translate("HelpWidget", u"Find ...", None))
        self.next_button.setText(QCoreApplication.translate("HelpWidget", u"Next", None))
        self.previous_button.setText(QCoreApplication.translate("HelpWidget", u"Previous", None))
        self.casesensitive_checkbox.setText(QCoreApplication.translate("HelpWidget", u"Case sensitive", None))
        self.wholewords_checkbox.setText(QCoreApplication.translate("HelpWidget", u"Whole words", None))
    # retranslateUi

