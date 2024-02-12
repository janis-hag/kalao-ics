from kalao.utils import ktools

import matplotlib.pyplot as plt

print('Subapertures idempotence')
for i in range(121):
    x, y = ktools.get_subaperture_2d(i)
    i_ = ktools.get_subaperture_1d(x, y)
    print(f'Subaperture {i:>3d} = ({x:>2d}, {y:>2d}) = {i_:>3d}')

print()

print('Actuators idempotence')
for i in range(140):
    x, y = ktools.get_actuator_2d(i)
    i_ = ktools.get_actuator_1d(x, y)
    print(f'Actuator {i:>3d} = ({x:>2d}, {y:>2d}) = {i_:>3d}')

plt.figure()
plt.imshow(ktools.get_wfs_flux_map(upsampling=16))
plt.title("WFS flux map")
plt.colorbar()

plt.figure()
plt.imshow(ktools.get_dm_flux_map(upsampling=16))
plt.title("DM flux map")
plt.colorbar()

plt.show()