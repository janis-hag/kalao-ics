import numpy as np


def cut(img, window, center=None, overflow='recenter'):
    hw = window // 2

    if center is None:
        cx, cy = [img.shape[0] // 2, img.shape[1] // 2]
    else:
        cx, cy = center

    if overflow == 'recenter':
        if cx + hw > img.shape[0]:
            cx = img.shape[0] - hw
        elif cx - hw < 0:
            cx = hw

        if cy + hw > img.shape[1]:
            cy = img.shape[1] - hw
        elif cy - hw < 0:
            cy = hw

    xs = cx - hw
    xe = cx + hw
    ys = cy - hw
    ye = cy + hw

    if xs < 0:
        xs = 0
    if xe > img.shape[0]:
        xe = img.shape[0]
    if ys < 0:
        ys = 0
    if ye > img.shape[1]:
        ye = img.shape[1]

    return img[xs:xe, ys:ye]


def percentile_clip(img, percentile_to_use):
    percentile_to_use = (100-percentile_to_use) / 2

    low = np.percentile(img, percentile_to_use)
    high = np.percentile(img, 100 - percentile_to_use)

    img = np.where(img < low, low, img)
    img = np.where(img > high, high, img)

    return img, low, high
