from typing import Type

import numpy as np

from PySide6.QtGui import QImage

from kalao.common.image import AbstractScale, LinearScale

from kalao.guis.utils import colormaps
from kalao.guis.utils.colormaps import Colormap

import config


def ndarray_to_qimage(img: np.ndarray | np.ma.masked_array, img_min: float |
                      None = None, img_max: float | None = None,
                      colormap: Colormap = colormaps.Grayscale(),
                      scale: Type[AbstractScale] = LinearScale) -> QImage:
    if len(img.shape) < 2:
        img = img[np.newaxis, :]

    img_scaled = ndarray_normalize(img, img_min=img_min, img_max=img_max,
                                   colormap=colormap, scale=scale)

    img_uint8 = np.require(img_scaled, np.uint8, 'C')
    image = QImage(img_uint8.data, img_uint8.shape[1], img_uint8.shape[0],
                   img_uint8.shape[1], QImage.Format.Format_Indexed8)
    image.setColorTable(colormap.table)

    return image


def ndarray_normalize(img: np.ndarray | np.ma.masked_array, img_min: float |
                      None = None, img_max: float | None = None,
                      colormap: Colormap = colormaps.Grayscale(),
                      scale: Type[AbstractScale] = LinearScale
                      ) -> np.ndarray | np.ma.masked_array:

    is_scalar = np.isscalar(img)

    if img_min is None:
        img_min = np.min(img)

    if img_max is None:
        img_max = np.max(img)

    delta = img_max - img_min

    scale_min = colormap.min
    scale_max = colormap.max

    if isinstance(img, np.ma.masked_array):
        mask = img.mask
        img = img.filled(img_min)
    else:
        mask = None

    if delta > config.epsilon:
        rescale = (scale_max-scale_min) / delta
        offset = img_min*rescale - scale_min

        img_scaled = img*rescale - offset
        img_scaled = np.clip(img_scaled, scale_min, scale_max)
        img_scaled = scale(scale_min, scale_max).scale(img_scaled)
        img_scaled = np.rint(img_scaled).astype(np.uint8)
    else:
        if is_scalar:
            img_scaled = colormap.no_data_value
        else:
            img_scaled = np.full(img.shape, colormap.no_data_value)

    if is_scalar:
        if colormap.saturation_low_color is not None and img <= img_min:
            img_scaled = colormap.saturation_low_value

        if colormap.saturation_high_color is not None and img >= img_max:
            img_scaled = colormap.saturation_high_value
    else:
        if colormap.saturation_low_color is not None:
            img_scaled[img <= img_min] = colormap.saturation_low_value

        if colormap.saturation_high_color is not None:
            img_scaled[img >= img_max] = colormap.saturation_high_value

    if mask is not None:
        if colormap.has_transparency:
            img_scaled[mask] = colormap.transparency_value
        else:
            img_scaled[mask] = colormap.no_data_value

    return img_scaled
