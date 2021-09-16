import os
import sys
import math
import time

# add the necessary path to find the folder kalao for import
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from kalao.plc import control

import numpy as np
from astropy.io import fits
from matplotlib import pyplot as plt
from configparser import ConfigParser


config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser = ConfigParser()
parser.read(config_path)
ExpTime = parser.getfloat('FLI','ExpTime')


def centre_on_target():

    while True:
        rValue = control.take_image(dit = ExpTime)
        image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        file_handling.save_tmp_picture(image_path)

        if rValue != 0:
            # print(rValue)
            # database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        x, y = find_star(image_path)

        if x != -1 and y != -1:
            # ? TODO send offset to telescope ?
            return 0

        # TODO set manual_align = True
        # TODO wait for observer input
        # TODO send gop message
        # TODO send offset to telescope


def find_star(image_path, spot_size=7, estim_error=0.05, nb_step=5):
    """

    :param image_path: path for the image to be centered (String)
    :param spot_size: size of the spot for the search of the star in pixel. Must be odd. (int)
    :param estim_error: margin of error for the Gaussian fitting (float)
    :param nb_step: Precision settings (int)
    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    tb = time.time()
    hdu_list = fits.open(image_path)
    hdu_list.info()
    image = hdu_list[0].data
    hdu_list.close()

    # middle of the spot
    mid = int(spot_size / 2)

    # ponderation matrix for score calcul
    p1, p2 = np.abs(np.mgrid[-mid: mid + 1, -mid: mid + 1])
    ponderation = p1 + p2
    ponderation[mid, mid] = 1

    # set the minimum brightness for a pixel to be considered in score calcul
    median = np.median(image)
    hist, bin_edges = np.histogram(image[~np.isnan(image)], bins=4096, range=(median - 10, median + 10))
    lumino = np.float32((hist * bin_edges[:-1]).sum() / hist.sum() * 10)

    # for each pixel, check if he's brighter than lumino, then check index limite
    # if all ok: divide spot around the pixel by the ponderation matrix
    # after that, score is a matrix with luminosity score of all pixel brighter than lumino
    shape = image.shape
    score = np.zeros((shape[0], shape[1]))
    for i in range(shape[0]):
        for j in range(shape[1]):
            if image[i, j] > lumino:
                if i + mid + 1 <= shape[0] and j + mid + 1 <= shape[1] and i - mid >= 0 and j - mid >= 0:
                    score[i, j] = np.divide(image[i - mid:i + mid + 1, j - mid:j + mid + 1], ponderation).sum()

    # find the max of score matrix and get coordonate of it
    # argmax return flat index, unravel_index return right format
    (y, x) = np.unravel_index(np.argmax(score), score.shape)
    star_spot = image[y - mid: y + mid + 1, x - mid: x + mid + 1]

    # create x,y component for gaussian calculation.
    # corresponds to the coordinates of the picture
    x_gauss, y_gauss = np.mgrid[0:spot_size, 0:spot_size]
    x_mean = np.average(y_gauss, weights=star_spot)
    y_mean = np.average(x_gauss, weights=star_spot)

    # standard deviation of the spot selected
    # from g(x,y) = A * e^(− a(x−x_mean)² − b(x−x_mean)(y−y_mean) − c(y−y_mean)²)
    # with a = (cos²(θ)/2σ² + sin²(θ)/2σ²)
    #      b = (sin(2θ)/2σ² − sin(2θ)/2σ²)
    #      c = (sin²(θ)/2σ² + cos²(θ)/2σ²)
    # for  θ = 0, we got:
    #      a = 1/2σ²
    #      b = 0
    #      c = 1/2σ²
    # then σ = sqrt( ((x−x_mean)² - (y−y_mean)²) / (2 * ln(g(x,y)/A))
    # nomina = (x−x_mean)² - (y−y_mean)²
    # denomi = 2*ln(g(x,y)/A)
    nomina = -(np.power(x_gauss - mid, 2) + np.power(y_gauss - mid, 2))
    denomi = 2 * np.log(np.divide(star_spot, star_spot[mid, mid]))
    denomi[mid, mid] = 1
    result = np.divide(nomina, denomi)
    # the stdev of the middle is 0 by def, so we put NaN and use np.nanmean
    result[mid, mid] = np.nan
    sigma = np.nanmean(np.sqrt(np.abs(result)))

    mean = np.mean(star_spot)

    opti = 1
    x_f, y_f = 0, 0
    i_f = 0
    rng_step = 1
    ampl = image[y, x]

    # divide the area around the center (x_mean, y_mean) into nb_step * nb_step points
    # and find the point that minimizes the difference between the approximate gaussian and star_spot
    # Then repeat 3 times zooming in on the selected point
    # For each try, check with variation of sigma.
    for _ in range(3):
        for i in np.arange(-1, 1, 0.2):
            a_c = 0.5 / ((sigma + i) ** 2)

            for j in np.linspace(-rng_step / 2, rng_step / 2, nb_step * 2 + 1)[1::2]:
                xdiff = (x_gauss - (y_mean + j)) ** 2

                for k in np.linspace(-rng_step / 2, rng_step / 2, nb_step * 2 + 1)[1::2]:
                    ydiff = (y_gauss - (x_mean + k)) ** 2
                    gauss = ampl * np.exp(-((a_c * xdiff) + (a_c * ydiff)))
                    ratio = np.mean(np.abs(star_spot - gauss)) / mean

                    if opti > ratio:
                        opti = ratio
                        x_f, y_f = x_mean + k, y_mean + j
                        i_f = i

        x_mean = x_f
        y_mean = y_f
        rng_step /= nb_step

    tf = time.time()
    print("time:", tf - tb)

    print("-----------------------")
    print("Center :", (x_f, y_f))
    print("std    :", sigma + i_f)
    print("lum min:", lumino)
    print("ratio  :", opti)
    print("-----------------------")

    if opti > estim_error:
        print("That's not enough.. Humain intervention needed !")
        return -1, -1

    x_star = x + x_f - mid
    y_star = y + y_f - mid

    return x_star, y_star

