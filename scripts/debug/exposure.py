from kalao.ics.utils import exposure

mag = 2
target_adu = 16384
filter = 'SDSS-g'

exptime = exposure.magnitude_to_exposure_time(mag, target_adu, filter)
adu = exposure.magnitude_to_adu(mag, exptime, filter)

print('Check idempotence:', target_adu, adu)