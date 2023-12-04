import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

lbds = np.arange(300, 1100, 0.01)

array = pd.read_csv(f'ML4720MB.csv').to_numpy()
QE = np.interp(lbds, array[:, 0], array[:, 1] / 100, left=0, right=0)

plt.figure(0)
plt.plot(lbds, QE)

print("Without Quantum Efficiency (QE)")

for f in ['g', 'r', 'i', 'z']:
    array = pd.read_csv(f'SDSS {f}-band filter.csv').to_numpy()

    if array[0, 0] > array[-1, 0]:
        array = np.flip(array, axis=0)

    lbds = np.arange(300, 1100, 0.01)
    trans = np.interp(lbds, array[:, 0], array[:, 1] / 100, left=0, right=0)

    pos = np.where(trans > 0.5)

    start = lbds[pos][0]
    end = lbds[pos][-1]

    print(
        f'Filter {f}: center={(start+end)/2:.2f}, fwhm={end-start:.2f} ({start:.2f}-{end:.2f})'
    )

    plt.figure(0)
    plt.plot(lbds, trans)

print()
print("With Quantum Efficiency (QE)")

for f in ['g', 'r', 'i', 'z']:
    array = pd.read_csv(f'SDSS {f}-band filter.csv').to_numpy()

    if array[0, 0] > array[-1, 0]:
        array = np.flip(array, axis=0)

    lbds = np.arange(300, 1100, 0.01)
    trans = np.interp(lbds, array[:, 0], array[:, 1] / 100, left=0,
                      right=0) * QE

    pos = np.where(trans > 0.5)

    start = lbds[pos][0]
    end = lbds[pos][-1]

    print(
        f'Filter {f}: center={(start+end)/2:.2f}, fwhm={end-start:.2f} ({start:.2f}-{end:.2f})'
    )

    plt.figure(1)
    plt.plot(lbds, trans)

print()
print("With Quantum Efficiency (QE) and Normalisation")
for f in ['g', 'r', 'i', 'z']:
    array = pd.read_csv(f'SDSS {f}-band filter.csv').to_numpy()

    if array[0, 0] > array[-1, 0]:
        array = np.flip(array, axis=0)

    lbds = np.arange(300, 1100, 0.01)
    trans = np.interp(lbds, array[:, 0], array[:, 1] / 100, left=0,
                      right=0) * QE

    trans /= trans.max()

    pos = np.where(trans > 0.5)

    start = lbds[pos][0]
    end = lbds[pos][-1]

    print(
        f'Filter {f}: center={(start+end)/2:.2f}, fwhm={end-start:.2f} ({start:.2f}-{end:.2f})'
    )

    plt.figure(2)
    plt.plot(lbds, trans)

plt.show()
