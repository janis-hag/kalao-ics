import numpy as np

from astropy.io import fits

from PySide6.QtCore import Slot

from kalao.cacao import toolbox

from guis.kalao.mixins import SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOGraphicsView, KalAOMainWindow

import config


class CalibrationWindow(KalAOMainWindow, SceneHoverMixin):
    def __init__(self, conf, loop, wfs_shape, dm_shape, parent=None):
        super().__init__(parent)

        self.conf = conf
        self.loop = loop
        self.wfs_shape = wfs_shape
        self.dm_shape = dm_shape

        self.streams = {}
        self.fits_data = {}
        self.streams_data = {}

        loadUi('calibration.ui', self)

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KalAOGraphicsView):
                attr.hovered.connect(self.hover_xyv_to_str)

        self.on_reload_button_clicked()
        self.on_mode_spinbox_valueChanged(self.mode_spinbox.value())

        self.show()

    def max_mode_number(self):
        s = np.inf

        if self.fits_data['DMmodes'] is not None:
            s = min(s, self.fits_data['DMmodes'].shape[0])
        if self.fits_data['modesWFS'] is not None:
            s = min(s, self.fits_data['modesWFS'].shape[0])
        if self.streams_data['DMmodes'] is not None:
            s = min(s, self.streams_data['DMmodes'].shape[2])
        if self.streams_data['modesWFS'] is not None:
            s = min(s, self.streams_data['modesWFS'].shape[2])

        return s - 1

    @Slot(bool)
    def on_reload_button_clicked(self, checked):
        self.fits_data['wfsref'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/wfsref.fits')
        self.fits_data['wfsrefc'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/wfsrefc.fits')
        self.fits_data['wfsmask'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/wfsmask.fits')
        self.fits_data['wfsmap'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/wfsmap.fits')
        self.fits_data['modesWFS'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/CMmodesWFS.fits')
        self.fits_data['dmmask'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/dmmask.fits')
        self.fits_data['dmmap'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/dmmap.fits')
        self.fits_data['DMmodes'] = fits.getdata(
            config.GUI.cacao_workdir /
            f'setupfiles/{self.conf}/conf/CMmodesDM.fits')

        self.streams_data['wfsref'] = self.get_stream_data(
            f'aol{self.loop}_wfsref', 2)
        self.streams_data['wfsrefc'] = self.get_stream_data(
            f'aol{self.loop}_wfsrefc', 2)
        self.streams_data['wfsmask'] = self.get_stream_data(
            f'aol{self.loop}_wfsmask', 2)
        self.streams_data['wfsmap'] = self.get_stream_data(
            f'aol{self.loop}_wfsmap', 2)
        self.streams_data['modesWFS'] = self.get_stream_data(
            f'aol{self.loop}_modesWFS', 3)
        self.streams_data['dmmask'] = self.get_stream_data(
            f'aol{self.loop}_dmmask', 2)
        self.streams_data['dmmap'] = self.get_stream_data(
            f'aol{self.loop}_dmmap', 2)
        self.streams_data['DMmodes'] = self.get_stream_data(
            f'aol{self.loop}_DMmodes', 3)

        self.mode_spinbox.setMaximum(self.max_mode_number())

    def get_stream_data(self, stream_name, dim):
        stream = toolbox.open_stream_once(stream_name, self.streams)

        if stream is None:
            return None

        data = stream.get_data(False)

        if len(data.shape) != dim:
            if dim == 2:
                return data.reshape((1, data.shape[0]))
            elif dim == 3:
                return data.reshape((1, data.shape[0], data.shape[1]))
            else:
                return data

        return data

    @Slot(int)
    def on_mode_spinbox_valueChanged(self, i):
        self.update_image_fits('wfsref')
        self.update_image_fits('wfsrefc')
        self.update_image_fits('wfsmask')
        self.update_image_fits('wfsmap')
        self.update_image_fits('dmmask')
        self.update_image_fits('dmmap')
        self.update_image_fits('DMmodes')
        self.update_image_fits('modesWFS')

        self.update_image_stream('wfsref')
        self.update_image_stream('wfsrefc')
        self.update_image_stream('wfsmask')
        self.update_image_stream('wfsmap')
        self.update_image_stream('dmmask')
        self.update_image_stream('dmmap')
        self.update_image_stream('DMmodes')
        self.update_image_stream('modesWFS')

    def update_image_fits(self, key):
        view = getattr(self, f'{key}_fits_view')

        if self.fits_data.get(key) is not None:
            if len(self.fits_data[key].shape) == 2:
                view.setImage(self.fits_data[key])
            else:
                view.setImage(
                    self.fits_data[key][self.mode_spinbox.value(), :, :])
        else:
            if 'dm' in key or 'DM' in key:
                shape = self.dm_shape
            else:
                shape = self.wfs_shape

            view.setImage(np.ones(shape))

    def update_image_stream(self, key):
        view = getattr(self, f'{key}_stream_view')

        if self.streams_data.get(key) is not None:
            if len(self.streams_data[key].shape) == 2:
                view.setImage(self.streams_data[key])
            else:
                view.setImage(
                    self.streams_data[key][:, :,
                                           self.mode_spinbox.value()])
        else:
            if 'dm' in key or 'DM' in key:
                shape = self.dm_shape
            else:
                shape = self.wfs_shape
            view.setImage(np.ones(shape))

    def info_point(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()
