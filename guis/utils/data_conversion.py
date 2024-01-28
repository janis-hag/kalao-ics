import numpy as np

from PySide6.QtGui import QImage

from kalao.utils.image import LinearScale

from guis.utils import colormaps

import config


def ndarray_to_qimage(img, img_min=None, img_max=None,
                      colormap=colormaps.Grayscale(), scale=LinearScale):
    if len(img.shape) < 2:
        img = img[np.newaxis, :]

    if img_min is None:
        img_min = img.min()

    if img_max is None:
        img_max = img.max()

    delta = img_max - img_min

    scale_min = colormap.min
    scale_max = colormap.max

    if colormap.color_saturation_high is not None:
        scale_max -= 0.4999

    if colormap.color_saturation_low is not None:
        scale_min += 0.4999

    if np.ma.is_masked(img):
        mask = img.mask
        img = img.filled()
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
        img_scaled = np.ones(img.shape) * colormap.no_data_value

    if mask is not None:
        if colormap.has_transparency:
            img_scaled[mask] = colormap.transparency_value
        else:
            img_scaled[mask] = colormap.no_data_value

    img_uint8 = np.require(img_scaled, np.uint8, 'C')
    image = QImage(img_uint8.data, img_uint8.shape[1], img_uint8.shape[0],
                   img_uint8.shape[1], QImage.Format_Indexed8)
    image.setColorTable(colormap.colormap)

    return image
