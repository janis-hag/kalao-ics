import math
from typing import Any

import numpy as np

from PySide6.QtCharts import QScatterSeries, QValueAxis
from PySide6.QtCore import QPointF, QSignalBlocker, QTimer, Slot
from PySide6.QtGui import QBrush, QFont, QIcon, QPen, Qt
from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QWidget

from compiled.ui_ao_calibration import Ui_AOCalibrationWindow

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import ascii2html, colormaps
from kalao.guis.utils.colormaps import CoolWarmTransparent
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import (BackendActionMixin, BackendDataMixin,
                                     SceneHoverMixin)
from kalao.guis.utils.widgets import KImageViewer, KMainWindow, KMessageBox


class AOCalibrationWindow(KMainWindow, SceneHoverMixin, BackendDataMixin,
                          BackendActionMixin):
    data_unit = ''
    data_scaling = 1
    data_precision = 2
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    def __init__(self, backend: AbstractBackend, conf: str, loop: int,
                 wfs_shape: tuple[int, ...], dm_shape: tuple[int, ...],
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.modes_data = {}

        self.conf = conf
        self.loop = loop
        self.wfs_shape = wfs_shape
        self.dm_shape = dm_shape

        self.ui = Ui_AOCalibrationWindow()
        self.ui.setupUi(self)

        self.resize(1200, 600)

        self.setWindowTitle(f'{conf.upper()} - {self.windowTitle()}')

        self.calibration_order = [
            'prepare',
            'mlat',
            'mkDMpokemodes',
            'takeref',
            'acqlinResp',
            'RMHdecode',
            'RMmkmask',
            'compCM',
            'load',
            'save_restore',
        ]

        if conf == 'ttmloop':
            self.latency_max = 20
            self.zRM_timer_interval = 1000
        else:
            self.latency_max = 5
            self.zRM_timer_interval = 100

        self.all_modes_widget = QWidget()
        self.DMmodes_tiled_view = KImageViewer(self.all_modes_widget)
        self.modesWFS_tiled_view = KImageViewer(self.all_modes_widget)

        layout = QHBoxLayout(self.all_modes_widget)
        layout.addWidget(self.DMmodes_tiled_view)
        layout.addWidget(self.modesWFS_tiled_view)

        layout.setStretch(0, 1)
        layout.setStretch(1, 2)

        ### Calibration tab

        with QSignalBlocker(self.ui.calib_combobox):
            self.ui.calib_combobox.addItem('Loaded')
            self.ui.calib_combobox.addItem('Saved')

        for key in dir(self.ui):
            attr = getattr(self.ui, key)

            if isinstance(attr, KImageViewer):
                attr.hovered.connect(self.hover_xyv_to_str)

                if key.startswith('modesWFS') or key.startswith(
                        'DMmodes') or key.startswith(
                            'wfsref') or key.startswith('wfsrefc'):
                    attr.updateColormap(colormaps.CoolWarm())

        self.hovered.connect(self.info_to_statusbar)

        self.on_refresh_button_clicked(False)

        ### Latency tab

        # Create Chart and set General Chart setting
        chart = self.ui.latency_plot.chart()
        chart.legend().hide()

        # Serie
        pen = QPen(Color.TRANSPARENT, 0, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        brush = QBrush(Color.BLUE, Qt.BrushStyle.SolidPattern)

        series = self.latency_series = QScatterSeries()
        series.setPen(pen)
        series.setBrush(brush)
        series.setMarkerSize(3)
        series.setName('Latency')
        series.setPointsVisible(True)
        chart.addSeries(series)

        # X Axis Settings
        axis_x = self.latency_axis_x = QValueAxis()
        axis_x.setTickCount(7)
        axis_x.setRange(-1, self.latency_max)
        axis_x.setTitleText('Latency [ms]')
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.latency_axis_y = QValueAxis()
        axis_y.setTickCount(5)
        axis_y.setRange(0, 1)
        axis_y.setTitleText('Signal [a.u.]')
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        ### Zonal Response Matrix tab

        self.ui.zRM_view.updateColormap(colormaps.CoolWarm())

        self.zRM_timer = QTimer(self)
        self.zRM_timer.setInterval(self.zRM_timer_interval)
        self.zRM_timer.timeout.connect(self.zRM_next_image)

        ### Logs tab

        self.ui.calibration_textedit.setFont(QFont('Roboto Mono'))
        self.ui.calibration_textedit.document().setDefaultStyleSheet(
            ascii2html.stylesheet)

        ### Common

        self.ui.calibration_loopname_label.updateText(
            loop_name=f'KalAO-{conf}')
        self.ui.calibration_loopnumber_label.updateText(loop_number=self.loop)

        self.step_post(None, None)

        self.ui.tabWidget.setCurrentIndex(0)

        self.show()
        self.center()

    def step_pre(self, step: str) -> None:
        getattr(self.ui, f'calibration_{step}_indicator').setStatus(
            Color.ORANGE, 'Running')

        self.ui.calibration_textedit.clear()

    def step_post(self, step: str, data: dict[str, Any]) -> None:
        if step is None:
            step_index = -1
        else:
            step_index = self.calibration_order.index(step)

        sucess = data is None or data['returncode'] == 0

        if 0 <= step_index < len(self.calibration_order):
            key = self.calibration_order[step_index]

            if key == 'save_restore':
                pass
            else:
                if data is None:
                    pass
                else:
                    if sucess:
                        getattr(self.ui,
                                f'calibration_{key}_indicator').setStatus(
                                    Color.GREEN, 'Success')
                        if key == 'mlat':
                            i = self.ui.tabWidget.indexOf(self.ui.latency_tab)
                            self.ui.tabWidget.setTabEnabled(i, True)
                            self.ui.tabWidget.setCurrentIndex(i)
                        elif key == 'RMHdecode':
                            i = self.ui.tabWidget.indexOf(self.ui.zRM_tab)
                            self.ui.tabWidget.setTabEnabled(i, True)
                            self.ui.tabWidget.setCurrentIndex(i)
                        elif key == 'load':
                            i = self.ui.tabWidget.indexOf(
                                self.ui.calibration_tab)
                            self.ui.tabWidget.setCurrentIndex(i)
                            self.ui.calib_combobox.setCurrentText('Loaded')
                    else:
                        getattr(self.ui,
                                f'calibration_{key}_indicator').setStatus(
                                    Color.RED, 'Error')

                        i = self.ui.tabWidget.indexOf(self.ui.logs_tab)
                        self.ui.tabWidget.setCurrentIndex(i)

                    self.ui.calibration_textedit.appendHtml(
                        ascii2html.translate(data['stdout']))

                    horizontal_scrollbar = self.ui.calibration_textedit.horizontalScrollBar(
                    )
                    horizontal_scrollbar.setValue(0)

                    vertical_scrollbar = self.ui.calibration_textedit.verticalScrollBar(
                    )
                    vertical_scrollbar.setValue(vertical_scrollbar.maximum())

        def cleanup(key: str) -> None:
            if key == 'mlat':
                i = self.ui.tabWidget.indexOf(self.ui.latency_tab)
                self.ui.tabWidget.setTabEnabled(i, False)
            elif key == 'RMHdecode':
                i = self.ui.tabWidget.indexOf(self.ui.zRM_tab)
                self.ui.tabWidget.setTabEnabled(i, False)

        if step_index + 1 < len(self.calibration_order):
            key = self.calibration_order[step_index + 1]

            if key == 'save_restore':
                self.ui.calibration_save_restore_widget.setEnabled(True)
            else:
                key = self.calibration_order[step_index + 1]
                getattr(self.ui, f'calibration_{key}_button').setEnabled(True)
                getattr(self.ui, f'calibration_{key}_indicator').setStatus(
                    Color.BLACK, 'Ready')

                cleanup(key)

        if step_index + 2 < len(self.calibration_order):
            for key in self.calibration_order[step_index + 2:]:
                if key == 'save_restore':
                    self.ui.calibration_save_restore_widget.setEnabled(False)
                else:
                    getattr(self.ui,
                            f'calibration_{key}_button').setEnabled(False)
                    getattr(self.ui, f'calibration_{key}_indicator').setStatus(
                        Color.BLACK, 'Not ready')

                    cleanup(key)

        return sucess

    def calibration_check_return(self, data: dict[str, Any]) -> None:
        self.ui.calibration_textedit.clear()
        self.ui.calibration_textedit.appendHtml(data['stdout'])

        if data['returncode'] != 0:
            i = self.ui.tabWidget.indexOf(self.ui.logs_tab)
            self.ui.tabWidget.setCurrentIndex(i)

    ##### Calibration tab

    def update_modes_stats(self) -> None:
        self.modes_number = np.inf
        self.DMmodes_min = np.inf
        self.modes_dm_max = -np.inf
        self.modesWFS_min = np.inf
        self.modes_wfs_max = -np.inf

        if self.ui.calib_combobox.currentText() == 'Saved':
            data = self.modes_data.get('CMmodesDM', {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number, data.shape[0])
                self.DMmodes_min = min(self.DMmodes_min, data.min())
                self.modes_dm_max = max(self.modes_dm_max, data.max())

            data = self.modes_data.get('CMmodesWFS', {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number, data.shape[0])
                self.modesWFS_min = min(self.modesWFS_min, data.min())
                self.modes_wfs_max = max(self.modes_wfs_max, data.max())
        else:
            data = self.modes_data.get(f'aol{self.loop}_DMmodes',
                                       {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number,
                                        data.shape[len(data.shape) - 1])
                self.DMmodes_min = min(self.DMmodes_min, data.min())
                self.modes_dm_max = max(self.modes_dm_max, data.max())

            data = self.modes_data.get(f'aol{self.loop}_modesWFS',
                                       {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number,
                                        data.shape[len(data.shape) - 1])
                self.modesWFS_min = min(self.modesWFS_min, data.min())
                self.modes_wfs_max = max(self.modes_wfs_max, data.max())

        if np.isinf(self.modes_number):
            self.modes_number = 1

        self.ui.mode_spinbox.setMaximum(self.modes_number)
        self.ui.mode_spinbox.setSuffix(f' / {self.modes_number}')

    @Slot(bool)
    def on_all_modes_button_clicked(self, checked: bool) -> None:
        self.update_all_modes_images()
        self.all_modes_widget.show()
        self.all_modes_widget.resize(1500, 1000)

    @Slot(bool)
    def on_refresh_button_clicked(self, checked: bool) -> None:
        self.modes_data = self.action_send(self.ui.modes_widget,
                                           self.backend.ao_calibration_data,
                                           conf=self.conf, loop=self.loop)

        self.update_modes_stats()
        self.update_calib_images()
        self.update_all_modes_images()

    @Slot(int)
    def on_minmax_checkbox_stateChanged(self, state: Qt.CheckState) -> None:
        self.update_calib_images()

    @Slot(int)
    def on_calib_combobox_currentIndexChanged(self, index: int) -> None:
        self.update_modes_stats()
        self.update_calib_images()
        self.update_all_modes_images()

    @Slot(int)
    def on_mode_spinbox_valueChanged(self, i: int) -> None:
        self.update_calib_images()

    def update_calib_images(self) -> None:
        if self.ui.calib_combobox.currentText() == 'Saved':
            self.update_image('wfsref', 'wfsref', symetric=True)
            self.update_image('wfsrefc', 'wfsrefc', symetric=True)
            self.update_image('wfsmask', 'wfsmask')
            self.update_image('wfsmap', 'wfsmap')
            self.update_image('dmmask', 'dmmask')
            self.update_image('dmmap', 'dmmap')
            self.update_image('DMmodes', 'CMmodesDM', cube=True, symetric=True,
                              first_axis=True)
            self.update_image('modesWFS', 'CMmodesWFS', cube=True,
                              symetric=True, first_axis=True)
        else:
            self.update_image('wfsref', f'aol{self.loop}_wfsref',
                              symetric=True)
            self.update_image('wfsrefc', f'aol{self.loop}_wfsrefc',
                              symetric=True)
            self.update_image('wfsmask', f'aol{self.loop}_wfsmask')
            self.update_image('wfsmap', f'aol{self.loop}_wfsmap')
            self.update_image('dmmask', f'aol{self.loop}_dmmask')
            self.update_image('dmmap', f'aol{self.loop}_dmmap')
            self.update_image('DMmodes', f'aol{self.loop}_DMmodes', cube=True,
                              symetric=True, first_axis=False)
            self.update_image('modesWFS', f'aol{self.loop}_modesWFS',
                              cube=True, symetric=True, first_axis=False)

    def update_all_modes_images(self) -> None:
        if self.ui.calib_combobox.currentText() == 'Saved':
            self.create_images_tile(
                self.modes_data.get('CMmodesDM').get('data'),
                self.DMmodes_tiled_view, first_axis=True)
            self.create_images_tile(
                self.modes_data.get('CMmodesWFS').get('data'),
                self.modesWFS_tiled_view, first_axis=True)
        else:
            self.create_images_tile(
                self.modes_data.get(f'aol{self.loop}_DMmodes').get('data'),
                self.DMmodes_tiled_view, first_axis=False)
            self.create_images_tile(
                self.modes_data.get(f'aol{self.loop}_modesWFS').get('data'),
                self.modesWFS_tiled_view, first_axis=False)

    def create_images_tile(self, img: np.ndarray, view: KImageViewer,
                           first_axis: bool = True) -> None:
        if len(img.shape) < 3:
            img = img[np.newaxis, :]

        if first_axis:
            size = img.shape[0]
            img_i = img.shape[1]
            img_j = img.shape[2]
        else:
            img_i = img.shape[0]
            img_j = img.shape[1]
            size = img.shape[2]

        x = math.ceil(math.sqrt(size))
        y = math.ceil(size / x)

        img_full = np.full((img_i * y, img_j * x), np.nan)
        img_mask = np.full((img_i * y, img_j * x), False)

        for k in range(size):
            if first_axis:
                img_new = img[k, :, :]
            else:
                img_new = img[:, :, k]

            img_full[k // x * img_i:k//x*img_i + img_i,
                     k % x * img_j:k%x*img_j + img_j] = img_new

        for k in range(size, x * y):
            img_mask[k // x * img_i:k//x*img_i + img_i,
                     k % x * img_j:k%x*img_j + img_j] = np.full((img_i, img_j),
                                                                True)

        img_min = np.nanmin(img_full)
        img_max = np.nanmax(img_full)
        img_abs = max(abs(img_min), abs(img_max))

        view.updateColormap(CoolWarmTransparent())
        view.setImage(np.ma.masked_array(img_full, mask=img_mask),
                      img_min=-img_abs, img_max=img_abs)

    def update_image(self, view_key: str, data_key: str, cube: bool = False,
                     symetric: bool = False, first_axis: bool = True) -> None:
        view = getattr(self.ui, f'{view_key}_view')
        data = self.modes_data.get(data_key, {}).get('data')

        if data is not None:
            if not cube:
                img = data
            elif len(data.shape) == 2:
                img = data[self.ui.mode_spinbox.value() - 1, :]
            elif len(data.shape) == 3:
                if first_axis:
                    img = data[self.ui.mode_spinbox.value() - 1, :, :]
                else:
                    img = data[:, :, self.ui.mode_spinbox.value() - 1]
            else:
                raise Exception(
                    f'Unexpected image size {len(data.shape)} for {data_key}')

            img_min, img_max = self.compute_minmax(img, view_key, symetric)
            view.setImage(img, img_min, img_max)
        else:
            view.setImage(None)

    def compute_minmax(self, img: np.ndarray, view_key: str,
                       symetric: bool) -> tuple[float, float]:
        if self.ui.minmax_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()
        else:
            if view_key == 'DMmodes':
                img_min = self.DMmodes_min
                img_max = self.modes_dm_max
            elif view_key == 'modesWFS':
                img_min = self.modesWFS_min
                img_max = self.modes_wfs_max
            else:
                img_min = img.min()
                img_max = img.max()

        if symetric:
            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max
        else:
            img_min = 0

        return img_min, img_max

    @Slot(bool)
    def on_reload_button_clicked(self, checked: bool) -> None:
        data = self.action_send(self.ui.modes_widget,
                                self.backend.ao_calibration_reload,
                                conf=self.conf, loop=self.loop)

        self.calibration_check_return(data)

        self.on_refresh_button_clicked(False)

    ##### Latency tab

    def clear_latency_tab(self) -> None:
        self.ui.latency_framerate_spinbox.setValue(np.nan)
        self.ui.latency_frames_spinbox.setValue(np.nan)

        self.latency_series.clear()

        self.latency_axis_y.setRange(0, 1)

    ##### Calibration sequence tab

    @Slot(bool)
    def on_calibration_prepare_button_clicked(self, checked: bool) -> None:
        self.step_pre('prepare')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_prepare,
                                conf=self.conf, loop=self.loop)

        self.step_post('prepare', data)

    @Slot(bool)
    def on_calibration_mlat_button_clicked(self, checked: bool) -> None:
        # Clear data

        self.clear_latency_tab()

        self.step_pre('mlat')

        # Take measurement

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_mlat,
                                conf=self.conf, loop=self.loop)

        # Display data

        if not self.step_post('mlat', data):
            return

        framerateHz = self.consume_fps_param(data, f'mlat-{self.loop}',
                                             'out.framerateHz', force=True)
        if framerateHz is not None:
            self.ui.latency_framerate_spinbox.setValue(framerateHz)

        latencyfr = self.consume_fps_param(data, f'mlat-{self.loop}',
                                           'out.latencyfr', force=True)
        if latencyfr is not None:
            self.ui.latency_frames_spinbox.setValue(latencyfr)

        latency_data = data.get('hardwlatencypts')
        if latency_data is not None:
            if np.isnan(latency_data[:, 2]).all():
                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Icon.Critical)
                msgbox.setText('<b>Latency measurement failed!</b>')
                msgbox.setInformativeText(
                    'Even though the latency measurement succeeded, it only returned NaNs.'
                )
                msgbox.setModal(True)
                msgbox.show()
                return

            points = []
            for i in range(latency_data.shape[0]):
                points.append(
                    QPointF(latency_data[i, 1] * 1000, latency_data[i, 2]))

            self.latency_series.replace(points)
            self.latency_axis_y.setRange(0, latency_data[:, 2].max() * 1.05)

    @Slot(bool)
    def on_calibration_mkDMpokemodes_button_clicked(self,
                                                    checked: bool) -> None:
        self.step_pre('mkDMpokemodes')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_mkDMpokemodes,
                                conf=self.conf, loop=self.loop)

        self.step_post('mkDMpokemodes', data)

    @Slot(bool)
    def on_calibration_takeref_button_clicked(self, checked: bool) -> None:
        self.step_pre('takeref')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_takeref,
                                conf=self.conf, loop=self.loop)

        self.step_post('takeref', data)

    @Slot(bool)
    def on_calibration_acqlinResp_button_clicked(self, checked: bool) -> None:
        self.step_pre('acqlinResp')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_acqlinResp,
                                conf=self.conf, loop=self.loop)

        self.step_post('acqlinResp', data)

    @Slot(bool)
    def on_calibration_RMHdecode_button_clicked(self, checked: bool) -> None:
        self.step_pre('RMHdecode')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_RMHdecode,
                                conf=self.conf, loop=self.loop)

        if not self.step_post('RMHdecode', data):
            return

        img = self.consume_fits(data, 'zrespM-H')
        if img is not None:
            self.zRM_img = img
            self.zRM_min = img.min()
            self.zRM_max = img.max()

            with QSignalBlocker(self.ui.zRM_poke_spinbox):
                self.ui.zRM_poke_spinbox.setMaximum(img.shape[0])
                self.ui.zRM_poke_spinbox.setSuffix(f' / {img.shape[0]}')
                self.ui.zRM_poke_spinbox.setValue(1)

            self.update_zRM_view()

            self.ui.zRM_play_button.setChecked(True)
        else:
            self.zRM_img = None
            self.zRM_min = np.nan
            self.zRM_max = np.nan

            with QSignalBlocker(self.ui.zRM_poke_spinbox):
                self.ui.zRM_poke_spinbox.setMaximum(1)
                self.ui.zRM_poke_spinbox.setSuffix(' / --')
                self.ui.zRM_poke_spinbox.setValue(1)

    def zRM_next_image(self) -> None:
        with QSignalBlocker(self.ui.zRM_poke_spinbox):
            self.ui.zRM_poke_spinbox.setValue(
                self.ui.zRM_poke_spinbox.value() %
                self.ui.zRM_poke_spinbox.maximum() + 1)

            self.update_zRM_view()

    @Slot(bool)
    def on_zRM_play_button_toggled(self, checked: bool) -> None:
        if checked:
            self.ui.zRM_play_button.setIcon(
                QIcon(':/assets/icons/media-playback-start.svg'))
            self.zRM_timer.start()
        else:
            self.ui.zRM_play_button.setIcon(
                QIcon(':/assets/icons/media-playback-pause.svg'))
            self.zRM_timer.stop()

    @Slot(int)
    def on_zRM_minmax_checkbox_stateChanged(self,
                                            state: Qt.CheckState) -> None:
        self.update_zRM_view()

    @Slot(int)
    def on_zRM_poke_spinbox_valueChanged(self, i: int) -> None:
        self.ui.zRM_play_button.setChecked(False)

        self.update_zRM_view()

    def update_zRM_view(self) -> None:
        if self.zRM_img is None:
            return

        img = self.zRM_img[self.ui.zRM_poke_spinbox.value() - 1, :, :]

        if self.ui.zRM_minmax_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()
        else:
            img_min = self.zRM_min
            img_max = self.zRM_max

        abs_max = max(abs(img_min), abs(img_max))
        img_min = -abs_max
        img_max = abs_max

        self.ui.zRM_view.setImage(img, img_min, img_max)

    @Slot(bool)
    def on_calibration_RMmkmask_button_clicked(self, checked: bool) -> None:
        self.step_pre('RMmkmask')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_RMmkmask,
                                conf=self.conf, loop=self.loop)

        self.step_post('RMmkmask', data)

    @Slot(bool)
    def on_calibration_compCM_button_clicked(self, checked: bool) -> None:
        self.step_pre('compCM')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_compCM,
                                conf=self.conf, loop=self.loop)

        self.step_post('compCM', data)

    @Slot(bool)
    def on_calibration_load_button_clicked(self, checked: bool) -> None:
        self.step_pre('load')

        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_load,
                                conf=self.conf, loop=self.loop)

        self.step_post('load', data)

        self.on_refresh_button_clicked(False)

    @Slot(bool)
    def on_calibration_save_button_clicked(self, checked: bool) -> None:
        data = self.action_send(
            self.ui.calibration_buttons_widget,
            self.backend.ao_calibration_save, conf=self.conf, loop=self.loop,
            comment=self.ui.calibration_comment_lineedit.text())

        if self.calibration_check_return(data):
            return

        self.on_refresh_button_clicked(False)

    @Slot(bool)
    def on_calibration_restore_button_clicked(self, checked: bool) -> None:
        data = self.action_send(self.ui.calibration_buttons_widget,
                                self.backend.ao_calibration_reload,
                                conf=self.conf, loop=self.loop)

        if self.calibration_check_return(data):
            return

        self.on_refresh_button_clicked(False)
