# -*- coding: utf-8 -*-
# A few useful numbers (from OpticStudio):
#
# EUL PD = 1.2m
# TTM PD = 20e-3 m
# DM  PD = 4.4e-3 m
# WFS PD = 2.64e-3 m
#
# EUL WFNO = 11.9849
# WFS WFNO = 7.09899 (for ENPD = 1.2 m, 78.0889 for ENPD = 0.109091 m)
# FLI WFNO = 44.1023
#
# EUL EFL = 14.3819 m
# WFS EFL = 5.31532 m
# FLI EFL = 49.2726 m
#
# WFS Pixel size = 48e-6 m (2x2 binning)
# FLI Pixel size = 13e-6 m
#
# WFS Plate scale = 1.16 arcsec / px
# FlI Plate scale = 0.0507 arcsec / px

from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial

from kalao.utils import ktools

from kalao.definitions.enums import PLCStatus

kalao_ics_path = Path(__file__).absolute().parent
epsilon = 1e-12


class IPPower:
    url = 'http://10.10.132.94/statusjsn.js'

    class Port:
        RTC = 5
        Bench = 6
        BMC_DM = 7


class CalibUnit:
    velocity = 0.1  # mm/s

    position_min = 0  # mm
    position_max = 99  # mm


class ADC:
    velocity = 1  # °/s

    # Account for the clocking between the telescope and KalAO
    max_disp_offset = 0  # °

    # Angles on the ADC to have max vertical dispersion
    max_disp_angle_1 = -45.4437409 + max_disp_offset  # °
    max_disp_angle_2 = 45.4437409 - max_disp_offset  # °

    angle_threshold = 0.1  # °
    update_interval = 10  # s

    # These values come from the OpticStudio ADC design
    dispersion_reference_wavelength = 715e-9  # m
    dispersion = {
        450e-9:
            Polynomial([4.689e-2, 1.444e-5, -2.170e-6, 3.551e-9]) * 20 / 1200 *
            3600,  # ADC design start
        475e-9:
            Polynomial([3.795e-2, 1.169e-5, -1.756e-6, 2.874e-9]) * 20 / 1200 *
            3600,  # Sloan g'
        622e-9:
            Polynomial([8.897e-3, 2.739e-6, -4.117e-7, 6.738e-10]) * 20 /
            1200 * 3600,  # Sloan r'
        763e-9:
            Polynomial([-3.217e-3, -9.905e-7, 1.489e-7, -2.437e-10]) * 20 /
            1200 * 3600,  # Sloan i'
        905e-9:
            Polynomial([-1.013e-2, -3.119e-6, 4.689e-7, -7.675e-10]) * 20 /
            1200 * 3600,  # Sloan z'
        1018e-9:
            Polynomial([-1.375e-2, -4.233e-6, 6.364e-7, -1.042e-9]) * 20 /
            1200 * 3600,  # ADC design end
    }


class AO:
    cacao_workdir = Path('/home/kalao/kalao-cacao-workdir/')

    DM_loop_number = 1
    TTM_loop_number = 2

    # How long to wait after starting AO
    settling_time = 2

    wait_fps_run = 3  # s

    shwfs_algorithms = ['Quad-cell', 'Center of mass']
    bmc_stroke_modes = ['Mid-stroke', 'Minimize stroke']


class DM:
    # 1.75 um zernike coefficient on tip or tilt = 3.5um stroke (-1.75 to 1.75)
    # np.arctan(3.5e-6/4.4e-3) / 1.75 * 1000 = 0.455 mrad / um
    # 2 * 4.4 / 1200 / 1000 * 180/np.pi * 3600 = 1.51 arcsec / mrad
    plate_scale = 0.688  # arcsec / um


class TTM:
    # Should be 2 * 20 / 1200 / 1000 * 180/np.pi * 3600 = 6.88 arcsec / mrad
    plate_scale = 6.88  # arcsec / mrad

    # Recommended: 0.5 * 5 * 0.05 (10% of TTM range)
    offload_threshold = 0.25  # mrad
    offload_gain = 0.05  # -
    offload_interval = 1  # s

    # Recommended: 0.5 * 5 * 0.25 (25% of TTM range)
    max_tel_offload = 0.05  # arcsec


class FLI:
    ip = '127.0.0.1'
    port = 9080

    # Note: max exposure time is limited due to this timeout setting
    request_timeout = 3600  # s

    # Should be 1/(1.2*44.1023) * 3600 * 180/np.pi * 13e-6 = 0.0507 arcsec / px
    plate_scale = 0.0507  # arcsec / px

    center_x = 523  # px
    center_y = 543  # px

    median_bias = 1007  # ADU

    dummy_camera = False
    dummy_image_path = "/home/kalao/data/tmp_KALAO.2022-06-13T10:34:16.102.fits"

    laser_calib_power = 0.35  # mW
    laser_calib_exptime = 0.01  # s
    laser_calib_filter = 'nd'


class WFS:
    min_emgain = 1
    max_emgain = 1000
    min_exposuretime = 0
    max_exposuretime = 1000
    readouttime = 0.5538

    acquisition_time_timeout = 1
    acquisition_start_wait = 1

    # Should be 1/(1.2*7.09899) * 3600 * 180/np.pi * 48e-6 = 1.16 arcsec / px
    plate_scale = 1.16  # arcsec / px

    laser_calib_power = 8  # mW
    laser_calib_exptime = 1.5  # ms

    illumination_threshold = 1000  # ADU
    illumination_fraction = 0.5  # -

    # Flux at least 90%
    fully_illuminated_subaps = [
        4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 30,
        31, 34, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 51, 52, 53, 54,
        55, 56, 57, 58, 62, 63, 64, 65, 66, 67, 68, 69, 73, 74, 75, 76, 78, 79,
        80, 81, 82, 83, 84, 85, 86, 89, 90, 91, 92, 93, 94, 95, 96, 97, 101,
        102, 103, 104, 105, 106, 107, 114, 115, 116
    ]

    # Flux at least 15%
    all_illuminated_subaps = [
        3, 4, 5, 6, 7, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27,
        28, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,
        47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87,
        89, 90, 91, 92, 93, 94, 95, 96, 97, 100, 101, 102, 103, 104, 105, 106,
        107, 108, 113, 114, 115, 116, 117
    ]

    spots_file = AO.cacao_workdir / 'setupfiles/hw/KalAO-hwloop-rundir/spots_tel_pupil.txt'
    autogain_file = AO.cacao_workdir / 'setupfiles/hw/KalAO-hwloop-rundir/autogain_params.txt'

    # Default values, will be updated from spots_file at startup
    all_subaps = list(range(121))
    masked_subaps = [
        0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 20, 21, 22, 32, 33, 43, 48, 49, 50,
        59, 60, 61, 70, 71, 72, 77, 87, 88, 98, 99, 100, 108, 109, 110, 111,
        112, 113, 117, 118, 119, 120
    ]

    # Default values, will be updated from autogain_file at startup
    autogain_params = [(1, 0.5), (2, 0.5), (4, 0.5), (8, 0.5), (16, 0.5),
                       (32, 0.5), (64, 0.5), (128, 0.5), (256, 0.5),
                       (512, 0.5), (1000, 0.5), (1000, 1.0), (1000, 2.0),
                       (1000, 4.0), (1000, 8.0)]
    max_autogain_setting = len(autogain_params) - 1


class FilterWheel:
    device_port = '/dev/ttyUSB0'
    retries = 3  # -
    retry_wait = 2  # s

    position_list = ['clear', 'g', 'r', 'i', 'z', 'nd']

    filter_to_wavelength = {
        'g': 475e-9,  # m
        'r': 622e-9,  # m
        'i': 763e-9,  # m
        'z': 905e-9,  # m
        'clear': [450e-9, 1018e-9],  # m
        'nd': [450e-9, 1018e-9],  # m
    }

    filter_infos = {
        'g': {
            'name': 'SDSS g',
            'center': 465.47e-9,
            'fwhm': 131.71e-9,
            'start': 399.62e-9,
            'end': 531.33e-9,
        },
        'r': {
            'name': 'SDSS r',
            'center': 610.83e-9,
            'fwhm': 122.85e-9,
            'start': 549.41e-9,
            'end': 672.26e-9,
        },
        'i': {
            'name': 'SDSS i',
            'center': 758.10e-9,
            'fwhm': 123.69e-9,
            'start': 696.26e-9,
            'end': 819.95e-9,
        },
        'z': {
            'name': 'SDSS z',
            'center': np.nan,
            'fwhm': np.inf,
            'start': 822.80e-9,
            'end': np.inf,
        },
        'clear': {
            'name': 'Clear',
            'center': np.nan,
            'fwhm': np.inf,
            'start': 400e-9,
            'end': 1000e-9,
        },
        'nd': {
            'name': 'Neutral Density',
            'center': np.nan,
            'fwhm': np.nan,
            'start': np.nan,
            'end': np.nan,
        },
    }


class Laser:
    max_power = 8  # mW
    switch_wait = 10  # s
    position = 24.12  # mm


class Tungsten:
    switch_wait = 2  # s
    position = 88  # mm

    stabilisation_time = 300  # s
    stabilisation_poll_interval = 5  # s

    flat_exptime_list = {
        "clear": 300,  # s
        "g": 360,  # s
        "r": 480,  # s
        "i": 420,  # s
        "z": 420,  # s
        "nd": 300,  # s
    }


class PLC:
    ip = '10.10.132.121'
    port = 4840
    disabled = []

    # Calibration of the temperature sensors
    temp_bench_air_offset = -4.5  # °C, 19 - 23.5
    temp_bench_board_offset = -6.1  # °C, 19 - 25.1
    temp_water_in_offset = -3.6  # °C, 19 - 22.7
    temp_water_out_offset = -1.7  # °C, 19 - 20.3

    class Node:
        ADC1 = 'ns=4;s=MAIN.ADC1_Newport_PR50PP.motor'
        ADC2 = 'ns=4;s=MAIN.ADC2_Newport_PR50PP.motor'
        CALIB_UNIT = 'ns=4;s=MAIN.Linear_Standa_8MT'
        FLIP_MIRROR = 'ns=4;s=MAIN.Flip'
        SHUTTER = 'ns=4;s=MAIN.Shutter'
        TUNGSTEN = 'ns=4;s=MAIN.Tungsten'
        LASER = 'ns=4;s=MAIN.Laser'

        PUMP = 'ns=4;s=MAIN.bRelayPump'
        FAN = 'ns=4;s=MAIN.bRelayFan'
        HEATER = 'ns=4;s=MAIN.bWaterHeater'
        FLOWMETER = 'ns=4;s=MAIN.iFlowmeter'
        HYGROMETER = 'ns=4;s=MAIN.iHygrometer'

        TEMP_BENCH_AIR = 'ns=4;s=MAIN.Temp_Bench_Air'
        TEMP_BENCH_BOARD = 'ns=4;s=MAIN.Temp_Bench_Board'
        TEMP_WATER_IN = 'ns=4;s=MAIN.Temp_Water_In'
        TEMP_WATER_OUT = 'ns=4;s=MAIN.Temp_Water_Out'
        TEMP_PUMP = 'ns=4;s=MAIN.Temp_Pump'

    initial_pos = {
        Node.CALIB_UNIT: Laser.position,
        Node.ADC1: ADC.max_disp_angle_1 + 90,  # Zero dispersion
        Node.ADC2: ADC.max_disp_angle_2 + 90,  # Zero dispersion
    }


class SEQ:
    ip = "127.0.0.1"
    port = 5005
    gop_arg_int = []
    gop_arg_float = ["texp", "intensity", "mv"]
    gop_arg_string = ["filepath", "filterposition"]
    init_duration = 120
    T4_root = Path("/disks/synology")

    init_timeout = 500  # s

    # Pointing can be long when instrument change happens
    pointing_poll_interval = 2  # s
    pointing_timeout = 210  # s

    # Setup time to report to EDP
    timings = {
        'K_DARK': 15,  # s
        'K_LMPFLT': 15,  # s
        'K_SKYFLT': 20,  # s
        'K_TRGOBS': 20,  # s
        'K_FOCUS': 20,  # s
    }


class FITS:
    science_data_storage = Path('/gls/data/raw/kalao')
    focus_data_storage = science_data_storage / 'focus_sequences'
    temporary_data_storage = Path('/home/kalao/data/tmp/')

    last_image = science_data_storage / 'last_image.fits'
    last_focus_sequence = science_data_storage / 'last_focus_sequence.fits'

    file_mask = 0o440

    fits_default_header_file = kalao_ics_path / "definitions/fits_default_header.yaml"
    tcs_header_validity = 3600

    max_comment_length = 40
    max_length_without_HIERARCH = 8

    on_sky_types = ['K_SKYFLT', 'K_TRGOBS', 'K_FOCUS']

    base_header = {
        'K_DARK': {
            'DPR CATG': 'CALIB',
            'DPR TYPE': 'DARK',
            'PROG ID': '199',
            'OBS TARGET NAME': 'DARK'
        },
        'K_SKYFLT': {
            'DPR CATG': 'CALIB',
            'DPR TYPE': 'FLAT,SKY',
            'PROG ID': '199',
        },
        'K_LMPFLT': {
            'DPR CATG': 'CALIB',
            'DPR TYPE': 'FLAT,LAMP',
            'PROG ID': '199',
            'OBS TARGET NAME': 'LAMP'
        },
        'K_TRGOBS': {
            'DPR CATG': 'SCIENCE',
            'DPR TYPE': 'OBJECT',
        },
        'K_FOCUS': {
            'DPR CATG': 'CALIB',
            'DPR TYPE': 'FOCUS,OBJECT',
            'PROG ID': '199',
        },
        'K_TECH': {
            'DPR CATG': 'TECHNICAL',
        },
    }

    db_from_telheader = {
        'target_name': 'OBJECT',
        'target_ra': 'HIERARCH ESO TEL ALPHA',
        'target_dec': 'HIERARCH ESO TEL DELTA',
        'target_magnitude': 'HIERARCH ESO OBS TARG MV',
        'target_spt': 'HIERARCH ESO OBS TARG SP',
        'tel_focus_z': 'HIERARCH ESO TEL FOCU Z',
        'tel_mp_ie': 'HIERARCH ESO TEL MP IE',
        'tel_mp_ia': 'HIERARCH ESO TEL MP IA',
        'tel_m1_temp': 'HIERARCH ESO TEL M1 TEMP',
        'tel_m2_temp': 'HIERARCH ESO TEL M2 TEMP',
        'tel_ambi_dewp': 'HIERARCH ESO TEL AMBI DP',
        'tel_ambi_pressure': 'HIERARCH ESO TEL AMBI PRESS',
        'tel_ambi_relhum': 'HIERARCH ESO TEL AMBI RHUMP',
        'tel_ambi_temp': 'HIERARCH ESO TEL AMBI TEMP',
        'tel_windir': 'HIERARCH ESO TEL AMBI WINDDIR',
        'tel_windsp': 'HIERARCH ESO TEL AMBI WINDSP',
        'tel_led_status': 'HIERARCH ESO TEL LED',
    }


class Starfinder:
    min_peak = 500  # ADU

    # 40 px corresponds to 2 arcsec
    window = 40  # px


class Offsets:
    # Should be 13e-3 * 11.9849 / 44.1023 = 0.00353 mm / px
    fli_y_to_calibunit_mm = 0.00353  # mm / px

    # Should be 1/(1.2*44.1023) * 3600 * 180/np.pi * 13e-6 = 0.0507 arcsec / px
    fli_x_to_tel_alt = -0.0507  # arcsec / px
    fli_y_to_tel_az = 0.0507  # arcsec / px

    # Should be 0.5 * 1/(1.2*44.1023) * 1200 / 20 * 1000 * 13e-6 = 0.00737 mrad / px
    fli_x_to_ttm_tip = -0.00737  # mrad / px
    fli_y_to_ttm_tilt = 0.00737  # mrad / px

    # Should be 1/(1.2*7.09899) * 3600 * 180/np.pi * 48e-6 = 1.16 arcsec / px
    nuvu_x_to_tel_az = -1.16  # arcsec / px
    nuvu_y_to_tel_alt = 1.16  # arcsec / px

    # Should be 0.5 * 1/(1.2*7.09899) * 1200 / 20 * 1000 * 48e-6 = 0.169 mrad / px (2x2 binning)
    nuvu_x_to_ttm_tilt = -0.25807611836775707  # mrad / px
    nuvu_y_to_ttm_tip = 0.28649303833986856  # mrad / px

    # Should be 2 * 20 / 1200 / 1000 * 180/np.pi * 3600 = 6.88 arcsec / mrad
    ttm_tip_to_tel_alt = 6.88  # arcsec / mrad
    ttm_tilt_to_tel_az = 6.88  # arcsec / mrad


class Centering:
    automatic_timeout = 300  # s
    manual_timeout = 600  # s

    fli_with_calibunit_max_iter = 5  # -
    fli_with_calibunit_precision = 5  # px

    fli_with_telescope_max_iter = 5  # -
    fli_with_telescope_precision = 20  # px

    fli_with_ttm_max_iter = 5  # -
    fli_with_ttm_precision = 5  # px

    wfs_with_ttm_max_iter = 5  # -
    wfs_with_ttm_precision = 0.01  # px

    min_exptime = 5  # s


class Focusing:
    steps = 7  # -
    step_size = 50  # µm
    window_size = 80  # px

    autofocus_f0 = 29772  # µm
    autofocus_f1 = 32  # µm/°C
    autofocus_max_age = 3600  # s

    min_exptime = 20  # s


class Exposure:
    class Star:
        # TODO: to be refined
        mag_ref = 5  # visual magnitude
        exptime_ref = 1  # s
        adu_ref = 32768  # ADU
        fwhm_ref = 1  # arcsec

        # For finding optimal exposure time and filter for focusing and centering
        min_adu = 2048  # ADU
        max_adu = 32768  # ADU
        filter_list = ['clear', 'g', 'z']

    class SkyFlat:
        # TODO: to be refined
        exptime_ref = 10  # s
        adu_ref = 32768  # ADU

    filters_relative_flux = {
        'clear': 1,
        'g': 0.236,
        'r': 0.260,
        'i': 0.224,
        'z': 0.155,
    }


class Calib:
    class Flats:
        # yapf: disable
        default_flat_list = [
                "g", "g", "g", "g", "g",
                "r", "r", "r", "r", "r",
                "i", "i", "i", "i", "i",
                "z", "z", "z", "z", "z",
                "clear", "clear", "clear", "clear", "clear",
                "nd", "nd", "nd", "nd", "nd"
        ]
        # yapf: enable

        target_adu = 10000  # ADU
        min_exptime = 1  # s
        max_exptime = 300  # s

    class Darks:
        # How many darks to make for every exposure time
        dark_number = 5  # -


class Euler:
    latitude = -29.2594  # °
    longitude = -70.7331  # °
    altitude = 2375  # m
    default_pressure = 77200  # Pa
    default_temperature = 278.15  # K
    default_hygrometry = 0  # -


class GOP:
    ip = 'kalaortc01'  # 10.10.132.120
    port = 18234
    verbosity = 0


class Systemd:
    service_restart_wait = 15  # s

    services = {
        'FLI (Science Camera)': {
            'unit': 'kalao_fli.service',
            'enabled': True,
            'restart': False
        },
        'Nüvü (Wavefront Sensor)': {
            'unit': 'kalao_nuvu.service',
            'enabled': True,
            'restart': False
        },
        'CACAO': {
            'unit': 'kalao_cacao.service',
            'enabled': True,
            'restart': False,
            'reload-allowed': True
        },
        'Sequencer': {
            'unit': 'kalao_sequencer.service',
            'enabled': True,
            'restart': False  # Do NOT put to True (restart loop)
        },
        'GOP Server': {
            'unit': 'kalao_gop-server.service',
            'enabled': True,
            'restart': True
        },
        'Database Timer': {
            'unit': 'kalao_database-timer.service',
            'enabled': True,
            'restart': True
        },
        'Hardware Timer': {
            'unit': 'kalao_hardware-timer.service',
            'enabled': True,
            'restart': True
        },
        'Observation Timer': {
            'unit': 'kalao_observation-timer.service',
            'enabled': True,
            'restart': True
        },
        'GUI Backend': {
            'unit': 'kalao_gui-backend.service',
            'enabled': False,
            'restart': True
        },
    }


class Database:
    ip = 'localhost'
    port = 27017

    max_days = 3650  # days

    telemetry_update_interval = 10  # s
    monitoring_update_interval = 60  # s
    monitoring_min_update_interval = 5  # s


class ETCS:
    ip = '10.10.132.102'
    port = 10002
    token = 'ETCS_API_TOKEN_2023'
    request_timeout = 120

    temperature_file = '/disks/synology/gls/data/services/CURRENT/temperature_telescope.rdb'
    max_age = 120

    dummy_telescope = False


class Cooling:
    heater_hysteresis_temp = 2  # °C

    pump_restart_temp = 35  # °C
    max_pump_temperature = 60  # °C


class Timers:
    cooling_check_interval = 5  # s
    inactivity_check_interval = 30  # s

    inactivity_timeout = 2700  # s

    dm_wait_between_actions = 10  # s
    dm_sun_min_elevation = 6  # °


class GUI:
    ttm_plot_length = 300  # s

    logs_max_entries = 10000  # -
    logs_initial_entries = 1000  # -

    monitoring_max_age = 2 * max(Database.monitoring_update_interval,
                                 Database.telemetry_update_interval)  # s

    plots_mapping = {
        # -1
        'ERROR': -1,
        'UNKNOWN': -1,

        # 0
        False: 0,
        'OFF': 0,
        'CLOSED': 0,
        'DOWN': 0,

        # 1
        True: 1,
        'ON': 1,
        'OPEN': 1,
        'UP': 1,

        # PLC status
        PLCStatus.NOT_ENABLED: -1,
        PLCStatus.NOT_INITIALISED: -1,
        PLCStatus.INITIALISING: 0,
        PLCStatus.STANDING: 1,
        PLCStatus.MOVING: 2,
    }

    plots_exclude_list = [
        'observer_name', 'observer_email', 'fli_last_image_path',
        'fli_temporary_image_path', 'tcs_header_path',
        'filterwheel_filter_name', 'sequencer_command_received', 't120_host'
    ]

    refreshrate_streams = 10  # /s
    refreshrate_data = 1  # /s
    refreshrate_logs = 1  # /s
    refreshrate_focus = 1  # /s
    refreshrate_dbs = 1 / min(Database.monitoring_update_interval,
                              Database.telemetry_update_interval)  # /s

    http_port = 6666
    http_dataformat = 'application/octet-stream'


class FPS:
    NUVU = 'nuvu_acquire-1'
    SHWFS = 'shwfs_process-1'
    BMC = 'bmc_display-1'
    DMLOOP = 'mfilt-1'
    TTMLOOP = 'mfilt-2'


class Streams:
    NUVU_RAW = 'nuvu_raw'
    NUVU = 'nuvu_stream'
    FLI = 'fli_stream'
    SLOPES = 'shwfs_slopes'
    FLUX = 'shwfs_flux'
    DM = 'dm01disp'
    TTM = 'dm02disp'
    MODALGAINS = 'aol1_mgainfact'

    DM_FLAT = 'dm01disp00'
    DM_LOOP = 'dm01disp03'
    DM_REGISTRATION = 'dm01disp08'
    DM_NCPA = 'dm01disp09'
    DM_TURBULENCES = 'dm01disp10'
    DM_USER_CONTROLLED = 'dm01disp11'

    TTM_LOOP = 'dm02disp03'
    TTM_CENTERING = 'dm02disp04'
    TTM_USER_CONTROLLED = 'dm02disp11'


class StreamInfo:
    nuvu_stream = {'shape': (64, 64), 'min': 0, 'max': 2**16 - 1}
    fli_stream = {'shape': (1024, 1024), 'min': 0, 'max': 2**16 - 1}
    shwfs_slopes = {'shape': (11, 22), 'min': -2, 'max': 2}
    shwfs_flux = {'shape': (11, 11), 'min': 0, 'max': 2**16 - 1}
    dm01disp = {'shape': (12, 12), 'min': -1.75, 'max': 1.75}
    dm02disp = {'shape': (2, ), 'min': -2.5, 'max': 2.5}


if WFS.spots_file.exists():
    WFS.all_subaps, WFS.active_subaps, WFS.masked_subaps = ktools.read_spots_file(
        WFS.spots_file)
else:
    print(
        f'CONFIG | [WARNING] {WFS.spots_file} does not exists, using default value in config (may not be up-to-date)'
    )

if WFS.autogain_file.exists():
    WFS.autogain_params = ktools.read_autogain_file(WFS.autogain_file)
    WFS.max_autogain_setting = len(WFS.autogain_params) - 1
else:
    print(
        f'CONFIG | [WARNING] {WFS.autogain_file} does not exists, using default value in config (may not be up-to-date)'
    )
