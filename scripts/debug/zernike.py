from kalao.utils import zernike

import matplotlib.pyplot as plt

coeffs = [1, 0.5, 4, 0.2, -0.4, -2]

fig, axs = plt.subplots(1, 3)

pattern = zernike.generate_pattern(coeffs, (12, 12))
slopes = zernike.generate_slopes(coeffs, (11, 22))
slopes_from_pattern = zernike.slopes_from_pattern_interp(pattern)

axs[0].imshow(pattern, cmap='gray')
axs[1].imshow(slopes, cmap='gray')
axs[2].imshow(slopes_from_pattern, cmap='gray')

plt.show()