# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'part_find.ui'
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
    QPushButton, QSizePolicy, QWidget)
from . import rc_assets

class Ui_FindPart(object):
    def setupUi(self, FindPart):
        if not FindPart.objectName():
            FindPart.setObjectName(u"FindPart")
        FindPart.resize(699, 33)
        self.horizontalLayout = QHBoxLayout(FindPart)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.find_lineedit = QLineEdit(FindPart)
        self.find_lineedit.setObjectName(u"find_lineedit")
        self.find_lineedit.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.find_lineedit)

        self.next_button = QPushButton(FindPart)
        self.next_button.setObjectName(u"next_button")
        self.next_button.setEnabled(False)
        icon = QIcon()
        icon.addFile(u":/assets/icons/arrow-down.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.next_button.setIcon(icon)

        self.horizontalLayout.addWidget(self.next_button)

        self.previous_button = QPushButton(FindPart)
        self.previous_button.setObjectName(u"previous_button")
        self.previous_button.setEnabled(False)
        icon1 = QIcon()
        icon1.addFile(u":/assets/icons/arrow-up.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.previous_button.setIcon(icon1)

        self.horizontalLayout.addWidget(self.previous_button)

        self.casesensitive_checkbox = QCheckBox(FindPart)
        self.casesensitive_checkbox.setObjectName(u"casesensitive_checkbox")

        self.horizontalLayout.addWidget(self.casesensitive_checkbox)

        self.wholewords_checkbox = QCheckBox(FindPart)
        self.wholewords_checkbox.setObjectName(u"wholewords_checkbox")

        self.horizontalLayout.addWidget(self.wholewords_checkbox)


        self.retranslateUi(FindPart)

        QMetaObject.connectSlotsByName(FindPart)
    # setupUi

    def retranslateUi(self, FindPart):
        FindPart.setWindowTitle(QCoreApplication.translate("FindPart", u"Find", None))
        self.find_lineedit.setPlaceholderText(QCoreApplication.translate("FindPart", u"Find ...", None))
        self.next_button.setText(QCoreApplication.translate("FindPart", u"Next", None))
        self.previous_button.setText(QCoreApplication.translate("FindPart", u"Previous", None))
        self.casesensitive_checkbox.setText(QCoreApplication.translate("FindPart", u"Case sensitive", None))
        self.wholewords_checkbox.setText(QCoreApplication.translate("FindPart", u"Whole words", None))
    # retranslateUi

