import functools
from pathlib import Path

from PySide6.QtCore import QMetaObject
from PySide6.QtUiTools import QUiLoader

from guis.utils.widgets import (KChartView, KColorbar, KDateTimeEdit,
                                KDraggableChartView, KGraphicsView, KLabel,
                                KLineEdit, KNaNDoubleSpinbox,
                                KScaledDoubleSpinbox, KStatusIndicator,
                                KSvgWidget)

uipath = Path(__file__).absolute().parent.parent / 'uis'


def setEnabledStack(self, enabled, source):
    if enabled:
        if source in self._disable_stack:
            self._disable_stack.remove(source)

        if len(self._disable_stack) == 0:
            self.setEnabled(True)
    else:
        if source not in self._disable_stack:
            self._disable_stack.append(source)

            self.setEnabled(False)


class UiLoader(QUiLoader):
    def __init__(self, baseinstance, customWidgets=None):
        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

        self.registerCustomWidget(KLabel)
        self.registerCustomWidget(KLineEdit)
        self.registerCustomWidget(KGraphicsView)
        self.registerCustomWidget(KChartView)
        self.registerCustomWidget(KDraggableChartView)
        self.registerCustomWidget(KSvgWidget)
        self.registerCustomWidget(KDateTimeEdit)
        self.registerCustomWidget(KStatusIndicator)
        self.registerCustomWidget(KNaNDoubleSpinbox)
        self.registerCustomWidget(KScaledDoubleSpinbox)
        self.registerCustomWidget(KColorbar)

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.baseinstance:
            return self.baseinstance

        else:
            if class_name in self.availableWidgets():
                widget = QUiLoader.createWidget(self, class_name, parent, name)

                widget._disable_stack = []
                widget.setEnabledStack = functools.partial(
                    setEnabledStack, widget)

            else:
                try:
                    widget = self.customWidgets[class_name](parent)

                except (TypeError, KeyError):
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
