# -*- coding: utf-8 -*-

# All times in seconds


class PLC:
    ip = "10.10.132.121"
    port = 4840
    init_timeout = 200
    init_nb_try = 3
    disabled = []
    temp_bench_air_offset = -4.5  # °C, 19 - 23.5
    temp_bench_board_offset = -6.1  # °C, 19 - 25.1
    temp_water_in_offset = -3.6  # °C, 19 - 22.7
    temp_water_out_offset = -1.7  # °C, 19 - 20.3


class ADC:
    # Angles on the ADC to have max vertical dispersion
    max_disp_angle_1 = 314.556259  # °
    max_disp_angle_2 = 45.4437409  # °
    angle_threshold = 0.1  # °
    update_interval = 10  # s


class TTM:
    # Should be 2 * 20 / 1200 / 1000 * 180/np.pi * 3600 = 6.88 arcsec / mrad
    tip_to_onsky = 6.88  # arcsec / mrad
    tilt_to_onsky = 6.88  # arcsec / mrad

    # Recommended: 5 * 0.1 (10% of TTM range)
    offload_threshold = 0.5  # mrad
    offload_interval = 10  # s

    max_tel_offload = 0.75  # arcsec


class FLI:
    #science_data_storage   = "/home/kalao/data/science/"
    science_data_storage = "/gls/data/raw/kalao"
    temporary_data_storage = "/home/kalao/data/tmp/"
    file_mask = 0o440
    exp_time = 0.05
    setup_time = 4
    ip = "127.0.0.1"
    port = 9080

    # Max exposure time limited to 10 minutes due to this timeout setting
    request_timeout = 3500  # s

    # Should be 1/49.2726 * 3600 * 180/np.pi * 13e-6 = 0.0544 arcsec / px
    pix_scale_x = 0.0658  # arcsec / px
    pix_scale_y = 0.0512  # arcsec / px

    center_x = 551  # px
    #535
    center_y = 525  # px
    #520

    dummy_camera = False
    dummy_image_path = "/home/kalao/data/tmp_KALAO.2022-06-13T10:34:16.102.fits"
    temperature_warn_threshold = -29.8
    laser_calib_dit = 0.01


class FilterWheel:
    device_port = " /dev/ttyUSB0"
    # soon to be changed to /dev/fw102c
    enable_wait = 2.0  # s
    initialization_wait = 2.0  # s
    position_change_wait = 6.0  # s
    position_list = ['clear', 'g', 'r', 'i', 'z', 'nd']


class Laser:
    max_intensity = 10  # mW
    switch_wait = 5  # s
    position = 24.12  # mm
    calib_intensity = 1.5  # mW
    AO_calib_intensity = 3.5  # mW


class Tungsten:
    stabilisation_time = 300  # s
    position = 88  # mm
    switch_wait = 2  # s
    flat_dit_list = {
            "clear": 300,
            "g": 360,
            "r": 480,
            "i": 420,
            "z": 420,
            "nd": 300,
    }


class Calib:
    default_flat_list = [
            "g", "g", "g", "g", "g", "r", "r", "r", "r", "r", "i", "i", "i",
            "i", "i", "z", "z", "z", "z", "z", "clear", "clear", "clear",
            "clear", "clear", "nd", "nd", "nd", "nd", "nd"
    ]


class SEQ:
    ip = "127.0.0.1"
    port = 5005
    gop_arg_int = []
    gop_arg_float = ["dit", "intensity"]
    gop_arg_string = ["filepath", "filterposition"]
    init_duration = 120
    T4_root = "/disks/synology"
    fits_header_file = "/home/kalao/kalao-ics/definitions/fits_header.yaml"
    tcs_header_validity = 3600

    # Pointing can be long when instrument change happens
    pointing_wait_time = 2
    pointing_timeout = 210

    timings = {
            'DARK': 15,
            'LMPFLT': 15,
            'SKYFLT': 20,
            'TRGOBS': 20,
            'FOCUS': 20,
    }

    EDP_translate = {
            "texp": "dit",
            "centrage": "centering",
    }


class Starfinder:
    centering_timeout = 30
    #focusing_step = 0.1
    focusing_step = 0.01
    #focusing_step = 0.005
    focusing_pixels = 30
    focusing_dit = 20
    min_flux = 4096
    max_flux = 32768
    max_dit = 60
    dit_optimization_trials = 10
    FWHM = 30


class Euler:
    latitude = -29.2594  # °
    longitude = -70.7331  # °
    altitude = 2375  # m
    default_pressure = 77200  # Pa
    default_temperature = 278.15  # K


class GOP:
    ip = "kalaortc01"  # 10.10.132.120
    port = 18234
    verbosity = 0


class SystemD:
    camera_service = "kalao_camera.service"
    database_updater = "kalao_database-updater.service"
    flask_gui = "kalao_flask-gui.service"
    sequencer_service = "kalao_sequencer.service"
    gop_server = "kalao_gop_server.service"
    # temperature_control = "kalao_temperature-control.service"
    safety_watchdog = "kalao_safety-watchdog.service"
    # TODO: pump and loop services?
    service_restart_wait = 15


class Database:
    telemetry_update_interval = 10
    PLC_monitoring_update_interval = 60


class T120:
    connection_timeout = 5
    altaz_timeout = 10
    focus_timeout = 20
    host = "glslogin1.ls.eso.org"
    symb_name = "inter"
    rcmd = "ipcsrv"
    port = 12345
    semkey = 4000
    focus_offset_limit = 15
    temperature_file = "/disks/synology/gls/data/services/CURRENT/temperature_telescope.rdb"
    temperature_file_timeout = 120


class AO:
    WFS_illumination_threshold = 45000
    WFS_illumination_fraction = 0.8
    WFS_centering_precision = 0.1
    WFS_centering_timeout = 30
    WFS_centering_slope_threshold = 0.005

    # Should be 0.5 * 1/49.2726 * 1200 / 20 * 1000 * 13e-6 = 0.00792 mrad / px
    FLI_tip_to_TTM = 0.008497723325890764  # mrad / px
    FLI_tilt_to_TTM = 0.008497723325890764  # mrad / px

    # Should be 0.5 * 1/5.31532 * 1200 / 20 * 1000 * 48e-6 = 0.271 mrad / px (2x2 binning)
    WFS_tip_to_TTM = 0.28649303833986856  # mrad / px
    WFS_tilt_to_TTM = -0.25807611836775707  # mrad / px

    fully_illuminated_subaps = [
            14, 15, 16, 17, 18, 24, 25, 26, 27, 28, 29, 30, 34, 35, 36, 37, 38,
            40, 41, 42, 45, 46, 47, 51, 52, 53, 56, 57, 58, 62, 63, 64, 67, 68,
            69, 73, 74, 75, 78, 79, 80, 81, 82, 83, 84, 85, 86, 90, 91, 92, 93,
            94, 95, 96, 102, 103, 104, 105, 106
    ]
    all_illuminated_subaps = [
            4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29,
            30, 31, 34, 35, 36, 37, 38, 40, 41, 42, 44, 45, 46, 47, 51, 52, 53,
            54, 55, 56, 57, 58, 62, 63, 64, 65, 66, 67, 68, 69, 70, 72, 73, 74,
            75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86, 89, 90, 91, 92, 93, 94,
            95, 96, 97, 101, 102, 103, 104, 105, 106, 107, 114, 115, 116
    ]


class Cooling:
    minimal_flow = 0.5
    #0.28
    flow_warn = 1.2
    #0.35
    flow_grace_time = 120  # s
    max_water_temp = 28  # °C
    max_heatsink_temp = 35  # °C
    heatsink_temp_warn = 30  # °C
    max_CCD_temp = -25  # °C


class Watchdog:
    temperature_update_interval = 5
    bench_update_interval = 30
    inactivity_timeout = 2700
    open_shutter_timeout = 2700
