from typing import Any

import numpy as np

from PySide6.QtCore import QSignalBlocker, Slot
from PySide6.QtGui import Qt, QTextCursor, QTextDocument
from PySide6.QtWidgets import QTextEdit, QWidget

from compiled.ui_part_find import Ui_FindPart
from compiled.ui_part_imgminmax import Ui_ImgMinMaxPart

from kalao.common.image import AbstractCut

from kalao.guis.utils.widgets import KImageViewer


class FindPart(QWidget):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.ui = Ui_FindPart()
        self.ui.setupUi(self)

        self.state = 'no-selection'
        self.start_from = ''
        self.first_search = True

    def setup(self, textedit: QTextEdit, start_from='', allow_wrap=True):
        self._textedit = textedit
        self.start_from = start_from
        self.allow_wrap = allow_wrap

        textedit.verticalScrollBar().valueChanged.connect(
            self.on_verticalscrollbar_valueChanged)

    @Slot(str)
    def on_find_lineedit_textEdited(self, text: str) -> None:
        if text == '':
            self.ui.next_button.setEnabled(False)
            self.ui.previous_button.setEnabled(False)
        else:
            self.ui.next_button.setEnabled(True)
            self.ui.previous_button.setEnabled(True)

        self._find('lineedit')

    @Slot(bool)
    def on_next_button_clicked(self, checked: bool) -> None:
        self._find('next')

    @Slot(bool)
    def on_previous_button_clicked(self, checked: bool) -> None:
        self._find('previous')

    @Slot(int)
    def on_casesensitive_checkbox_stateChanged(self,
                                               state: Qt.CheckState) -> None:
        self._find('casesensitive')

    @Slot(int)
    def on_wholewords_checkbox_stateChanged(self,
                                            state: Qt.CheckState) -> None:
        self._find('wholewords')

    def _find(self, source) -> None:
        search_text = self.ui.find_lineedit.text()
        flags: QTextDocument.FindFlag = QTextDocument.FindFlag(0)

        if search_text == '':
            cursor = self._textedit.textCursor()
            cursor.clearSelection()
            self._textedit.setTextCursor(cursor)
            self.state = 'no-selection'
            return

        # Handle start from start or end
        if source == 'next':
            pass
        elif source == 'previous':
            flags |= QTextDocument.FindFlag.FindBackward
        else:
            if self.state == 'no-selection' and self.first_search:
                if self.start_from == 'start':
                    self._textedit.moveCursor(QTextCursor.MoveOperation.Start)
                elif self.start_from == 'end':
                    self._textedit.moveCursor(QTextCursor.MoveOperation.End)
                    flags |= QTextDocument.FindFlag.FindBackward
            elif self.state == 'non-previous-or-next-only':
                if self.start_from == 'end':
                    flags |= QTextDocument.FindFlag.FindBackward

        if not (source == 'previous' or source == 'next'):
            # Move cursor by one in the correct direction, so we can match same text if needed
            if flags & QTextDocument.FindFlag.FindBackward:
                self._textedit.moveCursor(QTextCursor.MoveOperation.Right)
            else:
                self._textedit.moveCursor(QTextCursor.MoveOperation.Left)

        # Check checkboxes
        if self.ui.casesensitive_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self.ui.wholewords_checkbox.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords

        # Find
        found = self._textedit.find(search_text, flags)

        if not found and self.allow_wrap:
            if flags & QTextDocument.FindFlag.FindBackward:
                direction = QTextCursor.MoveOperation.End
            else:
                direction = QTextCursor.MoveOperation.Start

            self._textedit.moveCursor(direction)
            found = self._textedit.find(search_text, flags)

        if found:
            if source == 'previous' or source == 'next':
                self.state = 'previous-or-next'
            elif not (source == 'previous' or
                      source == 'next') and self.state != 'previous-or-next':
                self.state = 'non-previous-or-next-only'

            self.first_search = False

    def on_verticalscrollbar_valueChanged(self, value: int) -> None:
        if self.start_from == 'start' and value == self._textedit.verticalScrollBar(
        ).minimum():
            self.first_search = True
        elif self.start_from == 'end' and value == self._textedit.verticalScrollBar(
        ).maximum():
            self.first_search = True


class ImgMinMaxPart(QWidget):
    data_unit = ''
    data_scaling = 1
    data_precision = 0
    data_symetric = False

    autoscale_min = -np.inf
    autoscale_max = np.inf

    fullscale_min = -np.inf
    fullscale_max = np.inf

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.ui = Ui_ImgMinMaxPart()
        self.ui.setupUi(self)

        self.views = []

    def setup(self, view_list: KImageViewer | list[KImageViewer], unit,
              precision, scaling, spinbox_min, spinbox_max, fullscale_min,
              fullscale_max, symetric: bool = False) -> None:
        self.ui.min_spinbox.setSuffix(unit)
        self.ui.min_spinbox.setDecimals(precision)
        self.ui.min_spinbox.setMinimum(spinbox_min)
        self.ui.min_spinbox.setMaximum(self.ui.max_spinbox.value())

        self.ui.max_spinbox.setSuffix(unit)
        self.ui.max_spinbox.setDecimals(precision)
        self.ui.max_spinbox.setMaximum(spinbox_max)
        self.ui.max_spinbox.setMinimum(self.ui.min_spinbox.value())

        # self.ui.min_spinbox.setReadOnly(self.autoscale_button.isChecked())
        # self.ui.max_spinbox.setReadOnly(self.autoscale_button.isChecked())

        if not isinstance(view_list, list):
            view_list = [view_list]

        self.views = view_list
        self.fullscale_min = fullscale_min
        self.fullscale_max = fullscale_max
        self.data_symetric = symetric

    @Slot(float)
    def on_min_spinbox_valueChanged(self, d: float) -> None:
        self.ui.autoscale_button.setChecked(False)
        self.ui.fullscale_button.setChecked(False)

        self.ui.max_spinbox.setMinimum(d)

        for view in self.views:
            view.updateMinMax(self.ui.min_spinbox.value() / self.data_scaling,
                              self.ui.max_spinbox.value() / self.data_scaling)

    @Slot(float)
    def on_max_spinbox_valueChanged(self, d: float) -> None:
        self.ui.autoscale_button.setChecked(False)
        self.ui.fullscale_button.setChecked(False)

        self.ui.min_spinbox.setMaximum(d)

        for view in self.views:
            view.updateMinMax(self.ui.min_spinbox.value() / self.data_scaling,
                              self.ui.max_spinbox.value() / self.data_scaling)

    @Slot(bool)
    def on_autoscale_button_toggled(self, checked: bool) -> None:
        # self.ui.min_spinbox.setReadOnly(checked)
        # self.ui.max_spinbox.setReadOnly(checked)

        if checked:
            self.ui.fullscale_button.setChecked(False)

            if not np.isinf(self.autoscale_min) and not np.isinf(
                    self.autoscale_max):
                with QSignalBlocker(self.ui.min_spinbox):
                    self.ui.min_spinbox.setMaximum(self.autoscale_max *
                                                   self.data_scaling)
                    self.ui.min_spinbox.setValue(self.autoscale_min *
                                                 self.data_scaling)

                with QSignalBlocker(self.ui.max_spinbox):
                    self.ui.max_spinbox.setMinimum(self.autoscale_min *
                                                   self.data_scaling)
                    self.ui.max_spinbox.setValue(self.autoscale_max *
                                                 self.data_scaling)

                for view in self.views:
                    view.updateMinMax(self.autoscale_min, self.autoscale_max)

        #     self.ui.min_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        #     self.ui.max_spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        # else:
        #     self.ui.min_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        #     self.ui.max_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @Slot(bool)
    def on_fullscale_button_toggled(self, checked: bool) -> None:
        if checked:
            self.ui.autoscale_button.setChecked(False)

            with QSignalBlocker(self.ui.min_spinbox):
                self.ui.min_spinbox.setMaximum(self.fullscale_max *
                                               self.data_scaling)
                self.ui.min_spinbox.setValue(self.fullscale_min *
                                             self.data_scaling)

            with QSignalBlocker(self.ui.max_spinbox):
                self.ui.max_spinbox.setMinimum(self.fullscale_min *
                                               self.data_scaling)
                self.ui.max_spinbox.setValue(self.fullscale_max *
                                             self.data_scaling)

            for view in self.views:
                view.updateMinMax(self.fullscale_min, self.fullscale_max)

    def update_spinboxes_unit(self, unit: str, precision: int,
                              scaling: float) -> None:
        with QSignalBlocker(self.ui.min_spinbox):
            self.ui.min_spinbox.setMinimum(self.ui.min_spinbox.minimum() /
                                           self.data_scaling * scaling)
            self.ui.min_spinbox.setMaximum(self.ui.min_spinbox.maximum() /
                                           self.data_scaling * scaling)
            self.ui.min_spinbox.setValue(self.ui.min_spinbox.value() /
                                         self.data_scaling * scaling)
            self.ui.min_spinbox.setDecimals(precision)
            self.ui.min_spinbox.setSuffix(unit)

        with QSignalBlocker(self.ui.max_spinbox):
            self.ui.max_spinbox.setMinimum(self.ui.max_spinbox.minimum() /
                                           self.data_scaling * scaling)
            self.ui.max_spinbox.setMaximum(self.ui.max_spinbox.maximum() /
                                           self.data_scaling * scaling)
            self.ui.max_spinbox.setValue(self.ui.max_spinbox.value() /
                                         self.data_scaling * scaling)
            self.ui.max_spinbox.setDecimals(precision)
            self.ui.max_spinbox.setSuffix(unit)

        self.data_scaling = scaling
        self.data_unit = unit
        self.data_precision = precision

    def compute_min_max(self, img: np.ndarray, cuts: AbstractCut | None = None
                        ) -> tuple[float, float]:
        if cuts is None:
            img_min = img.min()
            img_max = img.max()
        else:
            img_min, img_max = cuts.cut(img)

        if self.data_symetric:
            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

        self.autoscale_min = img_min
        self.autoscale_max = img_max

        if self.ui.autoscale_button.isChecked():
            with QSignalBlocker(self.ui.min_spinbox):
                self.ui.min_spinbox.setMaximum(img_max * self.data_scaling)
                self.ui.min_spinbox.setValue(img_min * self.data_scaling)

            with QSignalBlocker(self.ui.max_spinbox):
                self.ui.max_spinbox.setMinimum(img_min * self.data_scaling)
                self.ui.max_spinbox.setValue(img_max * self.data_scaling)
        else:
            img_min = self.ui.min_spinbox.value() / self.data_scaling
            img_max = self.ui.max_spinbox.value() / self.data_scaling

        return img_min, img_max
