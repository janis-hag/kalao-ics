import pandas as pd

from kalao.fli import camera
from kalao.utils import file_handling

from kalao.definitions.enums import ReturnCode

import config

#ret, data = camera._send_request('empty',
#                                 params={'filepath': '/tmp/fli_empty.fits'})

#if ret == ReturnCode.CAMERA_OK:
#    fli_header = file_handling._header_from_fits('/tmp/fli_empty.fits')
#else:
#    fli_header = file_handling._header_empty()

df = pd.concat([
    #fli_header,
    file_handling._header_from_yml(config.FITS.fits_header_file),
    file_handling._header_from_db('obs', dt=None),
    file_handling._header_from_db('telemetry', dt=None),
    file_handling._header_from_db('monitoring', dt=None),
    #file_handling._clean_header(file_handling._header_from_last_telescope_header()
]).query('~index.duplicated(keep="last")')

df.loc['RA'].value = 0.
df.loc['DEC'].value = 0.
df.loc['HIERARCH ESO INS SHUT ST'].value = 'OPEN'

df = file_handling._dynamic_cards_update(df, 'K_TRGOBS')
df = file_handling._sort_header(df)

print(file_handling._header_to_string(df))
