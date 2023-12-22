# -*- coding: utf-8 -*-
# A few useful numbers (from OpticStudio):
#
# EUL PD = 1.2m
# TTM PD = 20e-3 m
# DM  PD = 4.4e-3 m
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

from kalao.utils import kalao_tools

from kalao.definitions.enums import TrackingStatus

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

    # Should be 13e-3 * 11.9849 / 44.1023 = 0.00353 mm / px
    px_to_mm = 0.00355
    initial_offset = 22.23


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


class DM:
    # 1.75 um zernike coefficient on tip or tilt = 3.5um stroke (-1.75 to 1.75)
    # np.arctan(3.5e-6/4.4e-3) / 1.75 * 1000 = 0.455 mrad / um
    # 2 * 4.4 / 1200 / 1000 * 180/np.pi * 3600 = 1.51 arcsec / mrad
    plate_scale = 0.688  # arcsec / um


class TTM:
    # Should be 2 * 20 / 1200 / 1000 * 180/np.pi * 3600 = 6.88 arcsec / mrad
    plate_scale = 6.88  # arcsec / mrad

    # For offloading
    tip_to_onsky = 6.88  # arcsec / mrad
    tilt_to_onsky = -6.88  # arcsec / mrad

    # Recommended: 0.5 * 5 * 0.05 (10% of TTM range)
    offload_threshold = 0.25  # mrad
    offload_gain = 0.05  # -
    offload_interval = 1  # s

    # Recommended: 0.5 * 5 * 0.25 (25% of TTM range)
    max_tel_offload = 0.05  # arcsec


class FLI:
    exp_time = 5.0
    ip = "127.0.0.1"
    port = 9080

    # Max exposure time limited to 10 minutes due to this timeout setting
    request_timeout = 3500  # s

    # Should be 1/(1.2*44.1023) * 3600 * 180/np.pi * 13e-6 = 0.0507 arcsec / px
    plate_scale = 0.0507  # arcsec / px

    # For offsets
    px_x_to_onsky = 0.0658  # arcsec / px
    px_y_to_onsky = 0.0512  # arcsec / px

    center_x = 505  # px 505
    center_y = 545  # px 545

    dummy_camera = False
    dummy_image_path = "/home/kalao/data/tmp_KALAO.2022-06-13T10:34:16.102.fits"

    laser_calib_power = 0.35  # mW
    laser_calib_dit = 0.01  # s
    laser_calib_filter = 'nd'


class WFS:
    max_emgain = 1000
    min_exposuretime = 0.5
    max_autogain_setting = 15

    # Should be 1/(1.2*7.09899) * 3600 * 180/np.pi * 48e-6 = 1.16 arcsec / px
    plate_scale = 1.16  # arcsec / px

    laser_calib_power = 8  # mW
    laser_calib_exptime = 1.5  # ms


class FilterWheel:
    device_port = "/dev/ttyUSB0"
    retries = 3  # -
    retry_wait = 2  # s
    enable_wait = 2  # s
    initialization_wait = 2  # s
    position_change_wait = 6  # s
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
    switch_wait = 5  # s
    position = 24.12  # mm


class Tungsten:
    stabilisation_time = 300  # s
    position = 88  # mm
    switch_wait = 2  # s
    flat_dit_list = {
        "clear": 300,  # s
        "g": 360,  # s
        "r": 480,  # s
        "i": 420,  # s
        "z": 420,  # s
        "nd": 300,  # s
    }


class PLC:
    ip = "10.10.132.121"
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


class Calib:
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

    flat_min_flux = 10000  # ADU

    dark_number = 5


class SEQ:
    ip = "127.0.0.1"
    port = 5005
    gop_arg_int = []
    gop_arg_float = ["dit", "intensity"]
    gop_arg_string = ["filepath", "filterposition"]
    init_duration = 120
    T4_root = Path("/disks/synology")

    init_timeout = 200  # s
    init_terminate_grace_time = 5  # s
    init_wait_kill = 1  # s

    # Pointing can be long when instrument change happens
    pointing_wait_time = 2  # s
    pointing_timeout = 210  # s

    # Setup time to report to EDP
    timings = {
        'K_DARK': 15,  # s
        'K_LMPFLT': 15,  # s
        'K_SKYFLT': 20,  # s
        'K_TRGOBS': 20,  # s
        'K_FOCUS': 20,  # s
    }

    EDP_translate = {
        "texp": "dit",
        "centrage": "auto_center",
    }


class FITS:
    science_data_storage = Path("/gls/data/raw/kalao")
    temporary_data_storage = Path("/home/kalao/data/tmp/")
    file_mask = 0o440

    fits_header_file = kalao_ics_path / "definitions/fits_default_header.yaml"
    tcs_header_validity = 3600

    max_comment_length = 40
    max_length_without_HIERARCH = 8

    on_sky_types = ['K_SKYFLT', 'K_TRGOBS', 'K_FOCUS']

    base_header = {
        'K_DARK': {
            'DPR CATG': 'CALIB',
            'DPR TYPE': 'DARK',
            'PROG ID': '199',
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
            'DPR TECH': 'IMAGE',
            'DPR CATG': 'TECHNICAL',
        },
    }

    db_from_telheader = {
        'target': 'OBJECT',
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
    centering_timeout = 30
    focusing_step = 10  # switched from mm to mum with new m2 drive 0.01
    focusing_pixels = 30
    focusing_dit = 20
    min_flux = 4096
    max_flux = 32768
    max_dit = 60
    dit_optimization_trials = 10

    AO_wait_settle = 2

    # For 1" seeing and with 0.0507"/px plate scale, should be 1 / 0.0507 = 20 px
    FWHM = 30  # px


class Euler:
    latitude = -29.2594  # °
    longitude = -70.7331  # °
    altitude = 2375  # m
    default_pressure = 77200  # Pa
    default_temperature = 278.15  # K
    default_hygrometry = 0  # -


class GOP:
    ip = "kalaortc01"  # 10.10.132.120
    port = 18234
    verbosity = 0


class Systemd:
    service_restart_wait = 15  # s

    services = {
        'nuvu': {
            'unit': "kalao_nuvu.service",
            'log': 'nuvu_log',
            'enabled': True,
            'restart': False
        },
        'cacao': {
            'unit': "kalao_cacao.service",
            'log': None,
            'enabled': True,
            'restart': False
        },
        'sequencer': {
            'unit': "kalao_sequencer.service",
            'log': 'sequencer_log',
            'enabled': True,
            'restart': False  # Do NOT put to True (restart loop)
        },
        'camera': {
            'unit': "kalao_camera.service",
            'log': 'fli_log',
            'enabled': True,
            'restart': True
        },
        'flask-gui': {
            'unit': "kalao_flask-gui.service",
            'log': 'flask_log',
            'enabled': False,
            'restart': True
        },
        'gop-server': {
            'unit': "kalao_gop-server.service",
            'log': 'gop_log',
            'enabled': True,
            'restart': True
        },
        'database-timer': {
            'unit': "kalao_database-timer.service",
            'log': 'database_timer_log',
            'enabled': True,
            'restart': True
        },
        'safety-timer': {
            'unit': "kalao_safety-timer.service",
            'log': 'safety_timer_log',
            'enabled': True,
            'restart': True
        },
        'loop-timer': {
            'unit': "kalao_loop-timer.service",
            'log': 'loop_timer_log',
            'enabled': True,
            'restart': True
        },
        'pump-timer': {
            'unit': "kalao_pump-timer.service",
            'log': 'pump_timer_log',
            'enabled': True,
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


class T120:
    connection_timeout = 5
    altaz_timeout = 10
    focus_timeout = 20
    ip = "10.10.132.102"
    http_port = 10002
    host = "glslogin1.ls.eso.org"
    port = 17001
    semkey = 4000
    symb_name = "inter"
    rcmd = "ipcsrv"
    request_timeout = 120
    port_loop_timer = 17002
    focus_offset_limit = 1500
    temperature_file = "/disks/synology/gls/data/services/CURRENT/temperature_telescope.rdb"
    temperature_file_timeout = 120
    dummy_telescope = False


class AO:
    WFS_illumination_threshold = 1000  # ADU
    WFS_illumination_fraction = 0.5  # -
    WFS_centering_timeout = 30  # s
    WFS_centering_slope_threshold = 0.005  # px

    cacao_workdir = Path('/home/kalao/kalao-cacao-workdir/')

    DM_loop_number = 1
    TTM_loop_number = 2

    # Should be 0.5 * 1/(1.2*44.1023) * 1200 / 20 * 1000 * 13e-6 = 0.00737 mrad / px
    FLI_tip_to_TTM = 0.008497723325890764  # mrad / px
    FLI_tilt_to_TTM = -0.008497723325890764  # mrad / px

    # Should be 0.5 * 1/(1.2*7.09899) * 1200 / 20 * 1000 * 48e-6 = 0.169 mrad / px (2x2 binning)
    WFS_tip_to_TTM = -0.28649303833986856  # mrad / px
    WFS_tilt_to_TTM = 0.25807611836775707  # mrad / px

    spots_file = Path(
        '/home/kalao/kalao-cacao-workdir/setupfiles/hw/KalAO-hwloop-rundir/spots_tel_pupil.txt'
    )

    flux_map = kalao_tools.get_wfs_flux_map()

    fully_illuminated_subaps = np.flatnonzero(flux_map > 0.9).tolist()
    all_illuminated_subaps = np.flatnonzero(flux_map > 0.15).tolist()

    all_subaps = list(range(121))
    masked_subaps = [
        0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 20, 21, 22, 32, 33, 43, 48, 49, 50,
        59, 60, 61, 70, 71, 72, 77, 87, 88, 98, 99, 100, 108, 109, 110, 111,
        112, 113, 117, 118, 119, 120
    ]

    wait_fps_run = 3  # s
    wait_camstack_start = 45  # s


class Cooling:
    heater_hysteresis_temp = 2  # °C

    pump_restart_temp = 35  # °C
    max_pump_temperature = 60  # °C


class Timers:
    temperature_check_interval = 5  # s
    bench_check_interval = 30  # s

    inactivity_timeout = 2700  # s

    dm_wait_between_actions = 10  # s
    dm_sun_min_elevation = 6  # °


class GUI:
    ttm_plot_length = 300  # s

    logs_lines = 10000  # -
    initial_logs_entries = 1000  # -

    plots_mapping = {
        # -1
        'ERROR': -1,

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

        # Tracking status
        TrackingStatus.IDLE: 0,
        TrackingStatus.POINTING: 1,
        TrackingStatus.CENTERING: 2,
        TrackingStatus.TRACKING: 3,
    }

    plots_exclude_list = ['observer_name', 'observer_email']

    refreshrate_streams = 10  # /s
    refreshrate_data = 1  # /s
    refreshrate_logs = 1  # /s
    refresharte_dbs = min(Database.monitoring_update_interval,
                          Database.telemetry_update_interval)

    http_port = 6666
    http_dataformat = 'pickle'


class FPS:
    NUVU = 'nuvu_acquire-1'
    SHWFS = 'shwfs_process-1'
    BMC = 'bmc_display-1'


class Streams:
    NUVU_RAW = 'nuvu_raw'
    NUVU = 'nuvu_stream'
    FLI = 'fli_stream'
    SLOPES = 'shwfs_slopes'
    FLUX = 'shwfs_slopes_flux'
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
    shwfs_slopes_flux = {'shape': (11, 11), 'min': 0, 'max': (2**16 - 1) * 4}
    dm01disp = {'shape': (12, 12), 'min': -1.75, 'max': 1.75}
    dm02disp = {'shape': (2, ), 'min': -2.5, 'max': 2.5}


if AO.spots_file.exists():
    AO.all_subaps, AO.active_subaps, AO.masked_subaps = kalao_tools.get_subapertures_from_file(
        AO.spots_file)
else:
    print(f'CONFIG | [WARNING] {AO.spots_file} does not exists')
