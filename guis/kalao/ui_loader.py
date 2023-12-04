from pathlib import Path

from PySide6.QtCore import QMetaObject
from PySide6.QtUiTools import QUiLoader

from guis.kalao.widgets import (KalAOChart, KalAODateTimeEdit,
                                KalAOGraphicsView, KalAOLabel, KalAOSvgWidget)

uipath = Path(__file__).absolute().parent.parent / 'ui'


class UiLoader(QUiLoader):
    def __init__(self, baseinstance, customWidgets=None):
        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

        self.registerCustomWidget(KalAOLabel)
        self.registerCustomWidget(KalAOGraphicsView)
        self.registerCustomWidget(KalAOChart)
        self.registerCustomWidget(KalAOSvgWidget)
        self.registerCustomWidget(KalAODateTimeEdit)

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.baseinstance:
            return self.baseinstance

        else:
            if class_name in self.availableWidgets():
                widget = QUiLoader.createWidget(self, class_name, parent, name)

            else:
                try:
                    widget = self.customWidgets[class_name](parent)

                except (TypeError, KeyError) as e:
                    raise Exception(
                        'No custom widget ' + class_name +
                        ' found in customWidgets param of UiLoader __init__.')

            if self.baseinstance:
                setattr(self.baseinstance, name, widget)

            return widget


def loadUi(uifile, baseinstance=None, customWidgets=None,
           workingDirectory=None):
    loader = UiLoader(baseinstance, customWidgets)

    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)

    widget = loader.load(str(uipath / uifile))
    QMetaObject.connectSlotsByName(widget)
    return widget
