import numpy as np

SIGMA_TO_HWHM = np.sqrt(2 * np.log(2))
SIGMA_TO_FWHM = 2 * np.sqrt(2 * np.log(2))


def is_triangular(T):
    n = round((np.sqrt(8*T + 1) - 1) / 2)

    return T == n * (n+1) // 2


def triangular_up_to(T):
    list = []
    n = 1

    while True:
        T_ = n * (n+1) // 2

        if T_ > T:
            break

        n += 1
        list.append(T_)

    return list


# yapf: disable
def gaussian_2d_rotated(x, y, mu_x = 0, mu_y = 0, sigma_x = 1, sigma_y = 1, theta = 0, A = None, C = 0):
    if A is None:
        A = 1/(sigma_x * sigma_y * 2*np.pi)

    a = np.cos(theta)**2/(2 * sigma_x**2) + np.sin(theta)**2/(2 * sigma_y**2)
    b = np.sin(2*theta)/(4 * sigma_x**2) - np.sin(2*theta)/(4 * sigma_y**2)
    c = np.sin(theta)**2/(2 * sigma_x**2) + np.cos(theta)**2/(2 * sigma_y**2)

    return A * np.exp(-(a*(x - mu_x)**2 + 2*b*(x - mu_x)*(y - mu_y) + c*(y - mu_y)**2)) + C
# yapf: enable
