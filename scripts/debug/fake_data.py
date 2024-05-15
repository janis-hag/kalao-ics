import time

from kalao.interfaces import fake_data

import matplotlib.pyplot as plt

start = time.monotonic()
dm_data = fake_data.dmdisp()
print(f'DM generation time: {time.monotonic() - start:3f}s')

start = time.monotonic()
wfs_data = fake_data.wfs_frame(dmdisp=dm_data)
print(f'Nuvu generation time: {time.monotonic() - start:3f}s')

start = time.monotonic()
slopes_data = fake_data.slopes(wfs_data)
print(f'Slopes generation time: {time.monotonic() - start:3f}s')

start = time.monotonic()
flux_data = fake_data.flux(wfs_data)
print(f'Flux generation time: {time.monotonic() - start:3f}s')

start = time.monotonic()
camera_data = fake_data.camera_frame(dmdisp=dm_data)
print(f'FLI generation time: {time.monotonic() - start:3f}s')

fig, axs = plt.subplots(2, 3)

axs[0, 0].imshow(dm_data, cmap='gray')
axs[0, 1].imshow(wfs_data, cmap='gray')
axs[0, 2].imshow(slopes_data, cmap='gray')
axs[1, 0].imshow(flux_data, cmap='gray')
axs[1, 1].imshow(camera_data, cmap='gray')

plt.show()