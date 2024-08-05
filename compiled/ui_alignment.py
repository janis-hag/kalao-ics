# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alignment.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMenuBar, QSizePolicy, QSpacerItem,
    QStatusBar, QWidget)

from kalao.guis.utils.widgets import KLabel

class Ui_AlignmentWindow(object):
    def setupUi(self, AlignmentWindow):
        if not AlignmentWindow.objectName():
            AlignmentWindow.setObjectName(u"AlignmentWindow")
        AlignmentWindow.resize(800, 600)
        self.centralwidget = QWidget(AlignmentWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupbox_1 = QGroupBox(self.centralwidget)
        self.groupbox_1.setObjectName(u"groupbox_1")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupbox_1.sizePolicy().hasHeightForWidth())
        self.groupbox_1.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QGridLayout(self.groupbox_1)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.groupbox_1, 0, 0, 1, 1)

        self.tb_ratio_label = KLabel(self.centralwidget)
        self.tb_ratio_label.setObjectName(u"tb_ratio_label")
        self.tb_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.tb_ratio_label, 4, 0, 1, 1)

        self.groupbox_2 = QGroupBox(self.centralwidget)
        self.groupbox_2.setObjectName(u"groupbox_2")
        sizePolicy.setHeightForWidth(self.groupbox_2.sizePolicy().hasHeightForWidth())
        self.groupbox_2.setSizePolicy(sizePolicy)
        self.gridLayout_3 = QGridLayout(self.groupbox_2)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.groupbox_2, 0, 1, 1, 1)

        self.groupbox_3 = QGroupBox(self.centralwidget)
        self.groupbox_3.setObjectName(u"groupbox_3")
        sizePolicy.setHeightForWidth(self.groupbox_3.sizePolicy().hasHeightForWidth())
        self.groupbox_3.setSizePolicy(sizePolicy)
        self.gridLayout_4 = QGridLayout(self.groupbox_3)
        self.gridLayout_4.setSpacing(0)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.groupbox_3, 1, 0, 1, 1)

        self.lr_ratio_label = KLabel(self.centralwidget)
        self.lr_ratio_label.setObjectName(u"lr_ratio_label")
        self.lr_ratio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.lr_ratio_label, 4, 1, 1, 1)

        self.average_label = KLabel(self.centralwidget)
        self.average_label.setObjectName(u"average_label")
        self.average_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.average_label, 2, 0, 1, 2)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.HLine)
        self.frame.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.frame, 3, 0, 1, 2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.poke_label = QLabel(self.centralwidget)
        self.poke_label.setObjectName(u"poke_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.poke_label.sizePolicy().hasHeightForWidth())
        self.poke_label.setSizePolicy(sizePolicy1)
        self.poke_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.poke_label)

        self.poke_spinbox = QDoubleSpinBox(self.centralwidget)
        self.poke_spinbox.setObjectName(u"poke_spinbox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.poke_spinbox.sizePolicy().hasHeightForWidth())
        self.poke_spinbox.setSizePolicy(sizePolicy2)
        self.poke_spinbox.setMaximum(1.750000000000000)
        self.poke_spinbox.setSingleStep(0.100000000000000)
        self.poke_spinbox.setValue(0.700000000000000)

        self.horizontalLayout.addWidget(self.poke_spinbox)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.label)

        self.states_combobox = QComboBox(self.centralwidget)
        self.states_combobox.setObjectName(u"states_combobox")
        sizePolicy2.setHeightForWidth(self.states_combobox.sizePolicy().hasHeightForWidth())
        self.states_combobox.setSizePolicy(sizePolicy2)
        self.states_combobox.setFrame(True)

        self.horizontalLayout.addWidget(self.states_combobox)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.gridLayout.addLayout(self.horizontalLayout, 6, 0, 1, 2)

        self.groupbox_4 = QGroupBox(self.centralwidget)
        self.groupbox_4.setObjectName(u"groupbox_4")
        sizePolicy.setHeightForWidth(self.groupbox_4.sizePolicy().hasHeightForWidth())
        self.groupbox_4.setSizePolicy(sizePolicy)
        self.gridLayout_5 = QGridLayout(self.groupbox_4)
        self.gridLayout_5.setSpacing(0)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)

        self.gridLayout.addWidget(self.groupbox_4, 1, 1, 1, 1)

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.HLine)
        self.frame_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.frame_2, 5, 0, 1, 2)

        AlignmentWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(AlignmentWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 30))
        AlignmentWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(AlignmentWindow)
        self.statusbar.setObjectName(u"statusbar")
        AlignmentWindow.setStatusBar(self.statusbar)

        self.retranslateUi(AlignmentWindow)

        QMetaObject.connectSlotsByName(AlignmentWindow)
    # setupUi

    def retranslateUi(self, AlignmentWindow):
        AlignmentWindow.setWindowTitle(QCoreApplication.translate("AlignmentWindow", u"Alignment", None))
        self.groupbox_1.setTitle(QCoreApplication.translate("AlignmentWindow", u"Actuator XX", None))
        self.tb_ratio_label.setText(QCoreApplication.translate("AlignmentWindow", u"Top/Bottom Flux Ratio: {tb_ratio:.2f}", None))
        self.groupbox_2.setTitle(QCoreApplication.translate("AlignmentWindow", u"Actuator XX", None))
        self.groupbox_3.setTitle(QCoreApplication.translate("AlignmentWindow", u"Actuator XX", None))
        self.lr_ratio_label.setText(QCoreApplication.translate("AlignmentWindow", u"Left/Right Flux Ratio: {lr_ratio:.2f}", None))
        self.average_label.setText(QCoreApplication.translate("AlignmentWindow", u"Average: {rs[0]:.3f}px @ {phis[0]:.0f}\u00b0 | {rs[1]:.3f}px @ {phis[1]:.0f}\u00b0 | {rs[2]:.3f}px @ {phis[2]:.0f}\u00b0 | {rs[3]:.3f}px @ {phis[3]:.0f}\u00b0", None))
        self.poke_label.setText(QCoreApplication.translate("AlignmentWindow", u"Poke amplitude:", None))
        self.label.setText(QCoreApplication.translate("AlignmentWindow", u"Show:", None))
        self.groupbox_4.setTitle(QCoreApplication.translate("AlignmentWindow", u"Actuator XX", None))
    # retranslateUi

