# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dm_channels.ui'
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
    QHBoxLayout, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QToolButton, QVBoxLayout, QWidget)

from kalao.guis.utils.widgets import (KImageViewer, KLabel, KScaledDoubleSpinbox)
from . import rc_assets

class Ui_DMChannelsWindow(object):
    def setupUi(self, DMChannelsWindow):
        if not DMChannelsWindow.objectName():
            DMChannelsWindow.setObjectName(u"DMChannelsWindow")
        DMChannelsWindow.resize(1202, 809)
        self.centralwidget = QWidget(DMChannelsWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(self.centralwidget)
        self.title_label.setObjectName(u"title_label")
        font = QFont()
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.title_label)

        self.scale_layout = QHBoxLayout()
        self.scale_layout.setObjectName(u"scale_layout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer)

        self.min_spinbox = KScaledDoubleSpinbox(self.centralwidget)
        self.min_spinbox.setObjectName(u"min_spinbox")
        self.min_spinbox.setKeyboardTracking(False)
        self.min_spinbox.setDecimals(2)
        self.min_spinbox.setMinimum(-99.000000000000000)
        self.min_spinbox.setMaximum(99.000000000000000)
        self.min_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.min_spinbox)

        self.minmax_label = QLabel(self.centralwidget)
        self.minmax_label.setObjectName(u"minmax_label")

        self.scale_layout.addWidget(self.minmax_label)

        self.max_spinbox = KScaledDoubleSpinbox(self.centralwidget)
        self.max_spinbox.setObjectName(u"max_spinbox")
        self.max_spinbox.setKeyboardTracking(False)
        self.max_spinbox.setDecimals(2)
        self.max_spinbox.setMinimum(-99.000000000000000)
        self.max_spinbox.setMaximum(99.000000000000000)
        self.max_spinbox.setSingleStep(0.100000000000000)

        self.scale_layout.addWidget(self.max_spinbox)

        self.horizontalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer_3)

        self.autoscale_button = QToolButton(self.centralwidget)
        self.autoscale_button.setObjectName(u"autoscale_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autoscale_button.sizePolicy().hasHeightForWidth())
        self.autoscale_button.setSizePolicy(sizePolicy)
        self.autoscale_button.setCheckable(True)
        self.autoscale_button.setChecked(True)

        self.scale_layout.addWidget(self.autoscale_button)

        self.horizontalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer_4)

        self.fullscale_button = QToolButton(self.centralwidget)
        self.fullscale_button.setObjectName(u"fullscale_button")
        sizePolicy.setHeightForWidth(self.fullscale_button.sizePolicy().hasHeightForWidth())
        self.fullscale_button.setSizePolicy(sizePolicy)
        self.fullscale_button.setCheckable(True)

        self.scale_layout.addWidget(self.fullscale_button)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.scale_layout.addItem(self.horizontalSpacer_5)


        self.verticalLayout.addLayout(self.scale_layout)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.commands_view = KImageViewer(self.centralwidget)
        self.commands_view.setObjectName(u"commands_view")
        self.commands_view.setEnabled(True)
        self.commands_view.setFrameShape(QFrame.Shape.NoFrame)
        self.commands_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.commands_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.commands_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.commands_view, 1, 2, 1, 1)

        self.commands_label = QLabel(self.centralwidget)
        self.commands_label.setObjectName(u"commands_label")
        self.commands_label.setFont(font)
        self.commands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.commands_label, 0, 2, 1, 1)

        self.dm_label = QLabel(self.centralwidget)
        self.dm_label.setObjectName(u"dm_label")
        self.dm_label.setFont(font)
        self.dm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.dm_label, 0, 0, 1, 1)

        self.dm_view = KImageViewer(self.centralwidget)
        self.dm_view.setObjectName(u"dm_view")
        self.dm_view.setEnabled(True)
        self.dm_view.setFrameShape(QFrame.Shape.NoFrame)
        self.dm_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.gridLayout.addWidget(self.dm_view, 1, 0, 1, 1)

        self.arrow_label = QLabel(self.centralwidget)
        self.arrow_label.setObjectName(u"arrow_label")
        font1 = QFont()
        font1.setPointSize(30)
        font1.setBold(False)
        self.arrow_label.setFont(font1)
        self.arrow_label.setMargin(10)

        self.gridLayout.addWidget(self.arrow_label, 1, 1, 1, 1)

        self.stroke_label_dm = KLabel(self.centralwidget)
        self.stroke_label_dm.setObjectName(u"stroke_label_dm")
        self.stroke_label_dm.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.stroke_label_dm, 2, 0, 1, 1)

        self.stroke_label_commands = KLabel(self.centralwidget)
        self.stroke_label_commands.setObjectName(u"stroke_label_commands")
        self.stroke_label_commands.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.stroke_label_commands, 2, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.reset_all_button = QPushButton(self.centralwidget)
        self.reset_all_button.setObjectName(u"reset_all_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.reset_all_button.sizePolicy().hasHeightForWidth())
        self.reset_all_button.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u":/assets/icons/refreshstructure.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.reset_all_button.setIcon(icon)

        self.verticalLayout.addWidget(self.reset_all_button, 0, Qt.AlignmentFlag.AlignHCenter)

        self.channels_layout = QGridLayout()
        self.channels_layout.setObjectName(u"channels_layout")
        self.layout_03 = QVBoxLayout()
        self.layout_03.setObjectName(u"layout_03")
        self.label_03 = QLabel(self.centralwidget)
        self.label_03.setObjectName(u"label_03")
        self.label_03.setFont(font)
        self.label_03.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_03.addWidget(self.label_03)

        self.info_label_03 = QLabel(self.centralwidget)
        self.info_label_03.setObjectName(u"info_label_03")
        self.info_label_03.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_03.addWidget(self.info_label_03)

        self.view_03 = KImageViewer(self.centralwidget)
        self.view_03.setObjectName(u"view_03")

        self.layout_03.addWidget(self.view_03)

        self.stroke_label_03 = KLabel(self.centralwidget)
        self.stroke_label_03.setObjectName(u"stroke_label_03")
        self.stroke_label_03.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_03.addWidget(self.stroke_label_03)

        self.reset_button_03 = QPushButton(self.centralwidget)
        self.reset_button_03.setObjectName(u"reset_button_03")
        sizePolicy1.setHeightForWidth(self.reset_button_03.sizePolicy().hasHeightForWidth())
        self.reset_button_03.setSizePolicy(sizePolicy1)
        self.reset_button_03.setIcon(icon)

        self.layout_03.addWidget(self.reset_button_03, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_03, 0, 3, 1, 1)

        self.layout_05 = QVBoxLayout()
        self.layout_05.setObjectName(u"layout_05")
        self.label_05 = QLabel(self.centralwidget)
        self.label_05.setObjectName(u"label_05")
        self.label_05.setFont(font)
        self.label_05.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_05.addWidget(self.label_05)

        self.info_label_05 = QLabel(self.centralwidget)
        self.info_label_05.setObjectName(u"info_label_05")
        self.info_label_05.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_05.addWidget(self.info_label_05)

        self.view_05 = KImageViewer(self.centralwidget)
        self.view_05.setObjectName(u"view_05")

        self.layout_05.addWidget(self.view_05)

        self.stroke_label_05 = KLabel(self.centralwidget)
        self.stroke_label_05.setObjectName(u"stroke_label_05")
        self.stroke_label_05.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_05.addWidget(self.stroke_label_05)

        self.reset_button_05 = QPushButton(self.centralwidget)
        self.reset_button_05.setObjectName(u"reset_button_05")
        sizePolicy1.setHeightForWidth(self.reset_button_05.sizePolicy().hasHeightForWidth())
        self.reset_button_05.setSizePolicy(sizePolicy1)
        self.reset_button_05.setIcon(icon)

        self.layout_05.addWidget(self.reset_button_05, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_05, 0, 5, 1, 1)

        self.layout_02 = QVBoxLayout()
        self.layout_02.setObjectName(u"layout_02")
        self.label_02 = QLabel(self.centralwidget)
        self.label_02.setObjectName(u"label_02")
        self.label_02.setFont(font)
        self.label_02.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_02.addWidget(self.label_02)

        self.info_label_02 = QLabel(self.centralwidget)
        self.info_label_02.setObjectName(u"info_label_02")
        self.info_label_02.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_02.addWidget(self.info_label_02)

        self.view_02 = KImageViewer(self.centralwidget)
        self.view_02.setObjectName(u"view_02")

        self.layout_02.addWidget(self.view_02)

        self.stroke_label_02 = KLabel(self.centralwidget)
        self.stroke_label_02.setObjectName(u"stroke_label_02")
        self.stroke_label_02.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_02.addWidget(self.stroke_label_02)

        self.reset_button_02 = QPushButton(self.centralwidget)
        self.reset_button_02.setObjectName(u"reset_button_02")
        sizePolicy1.setHeightForWidth(self.reset_button_02.sizePolicy().hasHeightForWidth())
        self.reset_button_02.setSizePolicy(sizePolicy1)
        self.reset_button_02.setIcon(icon)

        self.layout_02.addWidget(self.reset_button_02, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_02, 0, 2, 1, 1)

        self.layout_00 = QVBoxLayout()
        self.layout_00.setObjectName(u"layout_00")
        self.label_00 = QLabel(self.centralwidget)
        self.label_00.setObjectName(u"label_00")
        self.label_00.setFont(font)
        self.label_00.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_00.addWidget(self.label_00)

        self.info_label_00 = QLabel(self.centralwidget)
        self.info_label_00.setObjectName(u"info_label_00")
        self.info_label_00.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_00.addWidget(self.info_label_00)

        self.view_00 = KImageViewer(self.centralwidget)
        self.view_00.setObjectName(u"view_00")

        self.layout_00.addWidget(self.view_00)

        self.stroke_label_00 = KLabel(self.centralwidget)
        self.stroke_label_00.setObjectName(u"stroke_label_00")
        self.stroke_label_00.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_00.addWidget(self.stroke_label_00)

        self.reset_button_00 = QPushButton(self.centralwidget)
        self.reset_button_00.setObjectName(u"reset_button_00")
        sizePolicy1.setHeightForWidth(self.reset_button_00.sizePolicy().hasHeightForWidth())
        self.reset_button_00.setSizePolicy(sizePolicy1)
        self.reset_button_00.setIcon(icon)

        self.layout_00.addWidget(self.reset_button_00, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_00, 0, 0, 1, 1)

        self.layout_08 = QVBoxLayout()
        self.layout_08.setObjectName(u"layout_08")
        self.label_08 = QLabel(self.centralwidget)
        self.label_08.setObjectName(u"label_08")
        self.label_08.setFont(font)
        self.label_08.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_08.addWidget(self.label_08)

        self.info_label_08 = QLabel(self.centralwidget)
        self.info_label_08.setObjectName(u"info_label_08")
        self.info_label_08.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_08.addWidget(self.info_label_08)

        self.view_06 = KImageViewer(self.centralwidget)
        self.view_06.setObjectName(u"view_06")

        self.layout_08.addWidget(self.view_06)

        self.stroke_label_08 = KLabel(self.centralwidget)
        self.stroke_label_08.setObjectName(u"stroke_label_08")
        self.stroke_label_08.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_08.addWidget(self.stroke_label_08)

        self.reset_button_08 = QPushButton(self.centralwidget)
        self.reset_button_08.setObjectName(u"reset_button_08")
        sizePolicy1.setHeightForWidth(self.reset_button_08.sizePolicy().hasHeightForWidth())
        self.reset_button_08.setSizePolicy(sizePolicy1)
        self.reset_button_08.setIcon(icon)

        self.layout_08.addWidget(self.reset_button_08, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_08, 1, 2, 1, 1)

        self.layout_06 = QVBoxLayout()
        self.layout_06.setObjectName(u"layout_06")
        self.label_06 = QLabel(self.centralwidget)
        self.label_06.setObjectName(u"label_06")
        self.label_06.setFont(font)
        self.label_06.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_06.addWidget(self.label_06)

        self.info_label_06 = QLabel(self.centralwidget)
        self.info_label_06.setObjectName(u"info_label_06")
        self.info_label_06.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_06.addWidget(self.info_label_06)

        self.view_08 = KImageViewer(self.centralwidget)
        self.view_08.setObjectName(u"view_08")

        self.layout_06.addWidget(self.view_08)

        self.stroke_label_06 = KLabel(self.centralwidget)
        self.stroke_label_06.setObjectName(u"stroke_label_06")
        self.stroke_label_06.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_06.addWidget(self.stroke_label_06)

        self.reset_button_06 = QPushButton(self.centralwidget)
        self.reset_button_06.setObjectName(u"reset_button_06")
        sizePolicy1.setHeightForWidth(self.reset_button_06.sizePolicy().hasHeightForWidth())
        self.reset_button_06.setSizePolicy(sizePolicy1)
        self.reset_button_06.setIcon(icon)

        self.layout_06.addWidget(self.reset_button_06, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_06, 1, 0, 1, 1)

        self.layout_01 = QVBoxLayout()
        self.layout_01.setObjectName(u"layout_01")
        self.label_01 = QLabel(self.centralwidget)
        self.label_01.setObjectName(u"label_01")
        self.label_01.setFont(font)
        self.label_01.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_01.addWidget(self.label_01)

        self.info_label_01 = QLabel(self.centralwidget)
        self.info_label_01.setObjectName(u"info_label_01")
        self.info_label_01.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_01.addWidget(self.info_label_01)

        self.view_01 = KImageViewer(self.centralwidget)
        self.view_01.setObjectName(u"view_01")

        self.layout_01.addWidget(self.view_01)

        self.stroke_label_01 = KLabel(self.centralwidget)
        self.stroke_label_01.setObjectName(u"stroke_label_01")
        self.stroke_label_01.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_01.addWidget(self.stroke_label_01)

        self.reset_button_01 = QPushButton(self.centralwidget)
        self.reset_button_01.setObjectName(u"reset_button_01")
        sizePolicy1.setHeightForWidth(self.reset_button_01.sizePolicy().hasHeightForWidth())
        self.reset_button_01.setSizePolicy(sizePolicy1)
        self.reset_button_01.setIcon(icon)

        self.layout_01.addWidget(self.reset_button_01, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_01, 0, 1, 1, 1)

        self.layout_09 = QVBoxLayout()
        self.layout_09.setObjectName(u"layout_09")
        self.label_09 = QLabel(self.centralwidget)
        self.label_09.setObjectName(u"label_09")
        self.label_09.setFont(font)
        self.label_09.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_09.addWidget(self.label_09)

        self.info_label_09 = QLabel(self.centralwidget)
        self.info_label_09.setObjectName(u"info_label_09")
        self.info_label_09.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_09.addWidget(self.info_label_09)

        self.view_09 = KImageViewer(self.centralwidget)
        self.view_09.setObjectName(u"view_09")

        self.layout_09.addWidget(self.view_09)

        self.stroke_label_09 = KLabel(self.centralwidget)
        self.stroke_label_09.setObjectName(u"stroke_label_09")
        self.stroke_label_09.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_09.addWidget(self.stroke_label_09)

        self.reset_button_09 = QPushButton(self.centralwidget)
        self.reset_button_09.setObjectName(u"reset_button_09")
        sizePolicy1.setHeightForWidth(self.reset_button_09.sizePolicy().hasHeightForWidth())
        self.reset_button_09.setSizePolicy(sizePolicy1)
        self.reset_button_09.setIcon(icon)

        self.layout_09.addWidget(self.reset_button_09, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_09, 1, 3, 1, 1)

        self.layout_10 = QVBoxLayout()
        self.layout_10.setObjectName(u"layout_10")
        self.label_10 = QLabel(self.centralwidget)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font)
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_10.addWidget(self.label_10)

        self.info_label_10 = QLabel(self.centralwidget)
        self.info_label_10.setObjectName(u"info_label_10")
        self.info_label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_10.addWidget(self.info_label_10)

        self.view_10 = KImageViewer(self.centralwidget)
        self.view_10.setObjectName(u"view_10")

        self.layout_10.addWidget(self.view_10)

        self.stroke_label_10 = KLabel(self.centralwidget)
        self.stroke_label_10.setObjectName(u"stroke_label_10")
        self.stroke_label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_10.addWidget(self.stroke_label_10)

        self.reset_button_10 = QPushButton(self.centralwidget)
        self.reset_button_10.setObjectName(u"reset_button_10")
        sizePolicy1.setHeightForWidth(self.reset_button_10.sizePolicy().hasHeightForWidth())
        self.reset_button_10.setSizePolicy(sizePolicy1)
        self.reset_button_10.setIcon(icon)

        self.layout_10.addWidget(self.reset_button_10, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_10, 1, 4, 1, 1)

        self.layout_04 = QVBoxLayout()
        self.layout_04.setObjectName(u"layout_04")
        self.label_04 = QLabel(self.centralwidget)
        self.label_04.setObjectName(u"label_04")
        self.label_04.setFont(font)
        self.label_04.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_04.addWidget(self.label_04)

        self.info_label_04 = QLabel(self.centralwidget)
        self.info_label_04.setObjectName(u"info_label_04")
        self.info_label_04.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_04.addWidget(self.info_label_04)

        self.view_04 = KImageViewer(self.centralwidget)
        self.view_04.setObjectName(u"view_04")

        self.layout_04.addWidget(self.view_04)

        self.stroke_label_04 = KLabel(self.centralwidget)
        self.stroke_label_04.setObjectName(u"stroke_label_04")
        self.stroke_label_04.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_04.addWidget(self.stroke_label_04)

        self.reset_button_04 = QPushButton(self.centralwidget)
        self.reset_button_04.setObjectName(u"reset_button_04")
        sizePolicy1.setHeightForWidth(self.reset_button_04.sizePolicy().hasHeightForWidth())
        self.reset_button_04.setSizePolicy(sizePolicy1)
        self.reset_button_04.setIcon(icon)

        self.layout_04.addWidget(self.reset_button_04, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_04, 0, 4, 1, 1)

        self.layout_07 = QVBoxLayout()
        self.layout_07.setObjectName(u"layout_07")
        self.label_07 = QLabel(self.centralwidget)
        self.label_07.setObjectName(u"label_07")
        self.label_07.setFont(font)
        self.label_07.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_07.addWidget(self.label_07)

        self.info_label_07 = QLabel(self.centralwidget)
        self.info_label_07.setObjectName(u"info_label_07")
        self.info_label_07.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_07.addWidget(self.info_label_07)

        self.view_07 = KImageViewer(self.centralwidget)
        self.view_07.setObjectName(u"view_07")

        self.layout_07.addWidget(self.view_07)

        self.stroke_label_07 = KLabel(self.centralwidget)
        self.stroke_label_07.setObjectName(u"stroke_label_07")
        self.stroke_label_07.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_07.addWidget(self.stroke_label_07)

        self.reset_button_07 = QPushButton(self.centralwidget)
        self.reset_button_07.setObjectName(u"reset_button_07")
        sizePolicy1.setHeightForWidth(self.reset_button_07.sizePolicy().hasHeightForWidth())
        self.reset_button_07.setSizePolicy(sizePolicy1)
        self.reset_button_07.setIcon(icon)

        self.layout_07.addWidget(self.reset_button_07, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_07, 1, 1, 1, 1)

        self.layout_11 = QVBoxLayout()
        self.layout_11.setObjectName(u"layout_11")
        self.label_11 = QLabel(self.centralwidget)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font)
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_11.addWidget(self.label_11)

        self.info_label_11 = QLabel(self.centralwidget)
        self.info_label_11.setObjectName(u"info_label_11")
        self.info_label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_11.addWidget(self.info_label_11)

        self.view_11 = KImageViewer(self.centralwidget)
        self.view_11.setObjectName(u"view_11")

        self.layout_11.addWidget(self.view_11)

        self.stroke_label_11 = KLabel(self.centralwidget)
        self.stroke_label_11.setObjectName(u"stroke_label_11")
        self.stroke_label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_11.addWidget(self.stroke_label_11)

        self.reset_button_11 = QPushButton(self.centralwidget)
        self.reset_button_11.setObjectName(u"reset_button_11")
        sizePolicy1.setHeightForWidth(self.reset_button_11.sizePolicy().hasHeightForWidth())
        self.reset_button_11.setSizePolicy(sizePolicy1)
        self.reset_button_11.setIcon(icon)

        self.layout_11.addWidget(self.reset_button_11, 0, Qt.AlignmentFlag.AlignHCenter)


        self.channels_layout.addLayout(self.layout_11, 1, 5, 1, 1)


        self.verticalLayout.addLayout(self.channels_layout)

        self.verticalLayout.setStretch(2, 2)
        self.verticalLayout.setStretch(4, 3)
        DMChannelsWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(DMChannelsWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1202, 30))
        DMChannelsWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(DMChannelsWindow)
        self.statusbar.setObjectName(u"statusbar")
        DMChannelsWindow.setStatusBar(self.statusbar)

        self.retranslateUi(DMChannelsWindow)

        QMetaObject.connectSlotsByName(DMChannelsWindow)
    # setupUi

    def retranslateUi(self, DMChannelsWindow):
        DMChannelsWindow.setWindowTitle(QCoreApplication.translate("DMChannelsWindow", u"Deformable Mirror Channels - KalAO", None))
        self.title_label.setText(QCoreApplication.translate("DMChannelsWindow", u"Deformable Mirror Channels", None))
        self.minmax_label.setText(QCoreApplication.translate("DMChannelsWindow", u"\u2013", None))
        self.autoscale_button.setText(QCoreApplication.translate("DMChannelsWindow", u"Autoscale", None))
        self.fullscale_button.setText(QCoreApplication.translate("DMChannelsWindow", u"Fullscale", None))
        self.commands_label.setText(QCoreApplication.translate("DMChannelsWindow", u"Commands sent", None))
        self.dm_label.setText(QCoreApplication.translate("DMChannelsWindow", u"Commands computed by CACAO", None))
        self.arrow_label.setText(QCoreApplication.translate("DMChannelsWindow", u"\u2192", None))
        self.stroke_label_dm.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.stroke_label_commands.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_all_button.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset all", None))
        self.label_03.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 03", None))
        self.info_label_03.setText("")
        self.stroke_label_03.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_03.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_05.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 05", None))
        self.info_label_05.setText("")
        self.stroke_label_05.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_05.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_02.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 02", None))
        self.info_label_02.setText("")
        self.stroke_label_02.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_02.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_00.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 00", None))
        self.info_label_00.setText("")
        self.stroke_label_00.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_00.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_08.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 08", None))
        self.info_label_08.setText("")
        self.stroke_label_08.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_08.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_06.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 06", None))
        self.info_label_06.setText("")
        self.stroke_label_06.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_06.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_01.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 01", None))
        self.info_label_01.setText("")
        self.stroke_label_01.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_01.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_09.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 09", None))
        self.info_label_09.setText("")
        self.stroke_label_09.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_09.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_10.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 10", None))
        self.info_label_10.setText("")
        self.stroke_label_10.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_10.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_04.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 04", None))
        self.info_label_04.setText("")
        self.stroke_label_04.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_04.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_07.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 07", None))
        self.info_label_07.setText("")
        self.stroke_label_07.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_07.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
        self.label_11.setText(QCoreApplication.translate("DMChannelsWindow", u"Channel 11", None))
        self.info_label_11.setText("")
        self.stroke_label_11.setText(QCoreApplication.translate("DMChannelsWindow", u"{min:.2f}{unit} \u2013 {max:.2f}{unit}", None))
        self.reset_button_11.setText(QCoreApplication.translate("DMChannelsWindow", u"Reset channel", None))
    # retranslateUi

