import random
import time
from datetime import datetime

import numpy as np
import pandas as pd

from PySide6.QtCore import Signal

from kalao.interfaces import fake_data

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import LogType

import config


class FakeSHMFPSBackend(AbstractBackend):
    streams_and_fps_cache = {}

    def _update_stream(self, data, stream_name, stream, key=None):
        if key is None:
            key = stream_name

        cnt0 = data.get(stream_name, {}).get('cnt0', 0)

        data.update({
            key: {
                'updated': True,
                'cnt0': cnt0 + 1,
                'data': stream,
            }
        })

    def _update_params(self, data, fps_name, param_name, param):
        if data.get(fps_name) is None:
            data[fps_name] = {}

        if data.get(fps_name, {}).get(param_name, {}).get('cnt0') != param:
            data[fps_name].update({
                param_name: {
                    'updated': True,
                    'cnt0': param,
                    'value': param
                }
            })
        else:
            data[fps_name].update({
                param_name: {
                    'updated': False,
                    'value': None
                }
            })


class MainBackend(FakeSHMFPSBackend):
    ttm_data = np.array([0, 0])
    last_fli_update = 0
    first = True

    streams_updated = Signal(object)
    streams = {}

    data_updated = Signal(object)
    data = {}

    dmdisp_updated = Signal(object)
    dmdisp = {}

    @emit('streams_updated')
    @timeit
    def update_streams(self):
        dm_data = fake_data.dm()
        nuvu_data = fake_data.nuvu_frame(dmdisp=np.ma.getdata(dm_data))
        slopes_data = fake_data.slopes(nuvu_data)
        flux_data = fake_data.flux(nuvu_data)
        fli_data = fake_data.fli_frame(dmdisp=np.ma.getdata(dm_data))

        slopes_params = fake_data.slopes_params(slopes_data)
        flux_params = fake_data.flux_params(flux_data)

        self._update_stream(self.streams, config.Streams.DM, dm_data)
        self._update_params(self.streams, config.FPS.BMC, 'max_stroke', 0.9)

        self._update_stream(self.streams, config.Streams.NUVU, nuvu_data)

        self._update_stream(self.streams, config.Streams.SLOPES, slopes_data)
        self._update_params(self.streams, config.FPS.SHWFS, 'slope_x',
                            slopes_params['slope_x'])
        self._update_params(self.streams, config.FPS.SHWFS, 'slope_y',
                            slopes_params['slope_y'])
        self._update_params(self.streams, config.FPS.SHWFS, 'residual',
                            slopes_params['residual'])

        self._update_stream(self.streams, config.Streams.FLUX, flux_data)
        self._update_params(self.streams, config.FPS.SHWFS,
                            'flux_subaperture_avg',
                            flux_params['flux_subaperture_avg'])
        self._update_params(self.streams, config.FPS.SHWFS,
                            'flux_subaperture_brightest',
                            flux_params['flux_subaperture_brightest'])

        if time.monotonic() - self.last_fli_update > 10:
            self._update_stream(self.streams, config.Streams.FLI, fli_data)
            self.last_fli_update = time.monotonic()
        else:
            self._update_stream(self.streams, config.Streams.FLI, None)

        return self.streams

    @emit('data_updated')
    @timeit
    def update_data(self):
        self.ttm_data = fake_data.tiptilt(seed=self.ttm_data)

        self._update_stream(self.data, config.Streams.TTM, self.ttm_data)

        if self.first:
            self._update_stream(self.data, config.Streams.MODALGAINS,
                                np.ones((90, )))

            self._update_params(self.data, config.FPS.NUVU, 'autogain_on', 1)

            self._update_params(self.data, 'mfilt-1', 'loopON', 1)
            self._update_params(self.data, 'mfilt-1', 'loopgain', 0.8)
            self._update_params(self.data, 'mfilt-1', 'loopmult', 0.99)
            self._update_params(self.data, 'mfilt-1', 'looplimit', 1)

            self._update_params(self.data, 'mfilt-2', 'loopON', 0)
            self._update_params(self.data, 'mfilt-2', 'loopgain', 0.8)
            self._update_params(self.data, 'mfilt-2', 'loopmult', 0.99)
            self._update_params(self.data, 'mfilt-2', 'looplimit', 1)

            self.data['plc'] = {
                'shutter_state': 'CLOSED',
                'flip_mirror_position': 'DOWN',
                'calib_unit_position': 23.56,
                'laser_state': 'ON',
                'laser_power': 4.5,
                'tungsten_state': 'OFF',
                'adc1_angle': 135,
                'adc2_angle': 45,
                'filterwheel_filter_position': 4,
                'filterwheel_filter_name': 'z',
                'temp_bench_air': 18.2,
                'temp_bench_board': 18.1,
                'temp_water_in': 13,
                'temp_water_out': 15,
                'pump_status': 'ON',
                'pump_temp': 35,
                'heater_status': 'OFF',
                'fan_status': 'ON',
                'flow_value': 2.5
            }

            self.data['services'] = {
                'kalao_nuvu.service': ('active', 'exited',
                                       datetime(2023, 12, 4, 20, 15, 42,
                                                397363)),
                'kalao_cacao.service': ('active', 'exited',
                                        datetime(2023, 12, 7, 9, 15, 25,
                                                 886597)),
                'kalao_sequencer.service': ('active', 'running',
                                            datetime(2023, 12, 7, 10, 52, 17,
                                                     270106)),
                'kalao_camera.service': ('active', 'running',
                                         datetime(2023, 12, 7, 10, 52, 17,
                                                  901720)),
                'kalao_flask-gui.service': ('inactive', 'dead',
                                            datetime(1970, 1, 1, 0, 0)),
                'kalao_gop-server.service': ('active', 'running',
                                             datetime(2023, 12, 7, 10, 52, 17,
                                                      915063)),
                'kalao_database-timer.service':
                    ('active', 'running',
                     datetime(2023, 12, 7, 10, 52, 17, 921112)),
                'kalao_safety-timer.service':
                    ('active', 'running',
                     datetime(2023, 12, 7, 10, 52, 17, 931899)),
                'kalao_loop-timer.service': ('active', 'running',
                                             datetime(2023, 12, 7, 10, 52, 17,
                                                      932389)),
                'kalao_pump-timer.service': ('active', 'running',
                                             datetime(2023, 12, 7, 10, 52, 17,
                                                      943558))
            }

            self.first = False

        return self.data

    @emit('dmdisp_updated')
    @timeit
    def update_dmdisp(self, dm_number):
        if dm_number not in self.dmdisp:
            self.dmdisp[dm_number] = {}

        dm = f'dm{dm_number:02d}disp'

        if dm_number == 1:
            dm_data = fake_data.dm([0])

            for i in range(0, 12):
                channel = f'{dm}{i:02d}'

                channel_data = fake_data.dm()
                dm_data += channel_data

                self._update_stream(self.dmdisp[dm_number], channel,
                                    channel_data)

            self._update_stream(self.dmdisp[dm_number], dm, dm_data)
        else:
            dm_data = np.zeros((2, ))

            for i in range(0, 12):
                channel = f'{dm}{i:02d}'

                channel_data = fake_data.tiptilt()
                dm_data += channel_data

                self._update_stream(self.dmdisp[dm_number], channel,
                                    channel_data.reshape((1, 2)))

            self._update_stream(self.dmdisp[dm_number], dm,
                                dm_data.reshape((1, 2)))

        return self.dmdisp[dm_number]

    def get_plots_data(self, dt_start, dt_end, monitoring_keys, telemetry_keys,
                       obs_keys):
        timestamps = pd.date_range(dt_start, dt_end, 100)

        return {
            'monitoring':
                self._generate_plots_data(monitoring_keys, timestamps),
            'telemetry':
                self._generate_plots_data(telemetry_keys, timestamps),
            'obs':
                self._generate_plots_data(obs_keys, timestamps),
        }

    def _generate_plots_data(self, keys, timestamps):
        data = {}
        for key in keys:
            data[key] = {
                timestamp: value
                for timestamp, value in zip(
                    timestamps,
                    np.cumsum(np.random.normal(0, 1, len(timestamps))))
            }

        df = pd.DataFrame(data, columns=keys)

        return df

    ##### Loop controls

    # DM Loop

    def set_dm_loop_on(self, state):
        print(f'Set DM loop to {state} (virtually)')

    def set_dm_loop_gain(self, gain):
        print(f'Set DM gain to {gain} (virtually)')

    def set_dm_loop_mult(self, mult):
        print(f'Set DM mult to {mult} (virtually)')

    def set_dm_loop_limit(self, limit):
        print(f'Set DM limit to {limit} (virtually)')

    # TTM Loop

    def set_ttm_loop_on(self, state):
        print(f'Set TTM loop to {state} (virtually)')

    def set_ttm_loop_gain(self, gain):
        print(f'Set TTM gain to {gain} (virtually)')

    def set_ttm_loop_mult(self, mult):
        print(f'Set TTM mult to {mult} (virtually)')

    def set_ttm_loop_limit(self, limit):
        print(f'Set TTM limit to {limit} (virtually)')

    ##### Engineering

    def set_shutter_state(self, state):
        print(f'Set Shutter state to {state} (virtually)')

    def set_flipmirror_position(self, position):
        print(f'Set Flip Mirror position to {position} (virtually)')

    def set_calibunit_position(self, position):
        print(f'Set Calibration Unit position to {position} (virtually)')

    def set_tungsten_state(self, state):
        print(f'Set Tungsten state to {state} (virtually)')

    def set_laser_state(self, state):
        print(f'Set Laser state to {state} (virtually)')

    def set_laser_intensity(self, intensity):
        print(f'Set Laser intensity to {intensity} (virtually)')

    def set_filterwheel_filter(self, filter):
        print(f'Set Filter Wheel filter to {filter} (virtually)')

    def set_adc1_position(self, position):
        print(f'Set ADC1 position to {position} (virtually)')

    def set_adc2_position(self, position):
        print(f'Set ADC2 position to {position} (virtually)')

    def service_action(self, unit, action):
        print(f'Sent {action} to {unit} (virtually)')

    ##### DM channels

    def reset_dm(self, dm_number):
        print(f'Resetted DM {dm_number} (virtually)')

    def reset_channel(self, dm_number, channel):
        print(f'Resetted channel {channel} of DM {dm_number} (virtually)')

    ##### DM & TTM control

    def set_dm_to(self, array):
        print(f'Set DM to {array} (virtually)')

    def set_ttm_to(self, array):
        print(f'Set TTM to {array} (virtually)')

    ##### Logs

    def init_logs(self):
        logs = []

        for _ in range(config.GUI.initial_logs_entries):
            entry = self.generate_log()
            entry['text'] = '<span class="init">' + entry['text'] + '<span>'

            logs.append(entry)

        return logs

    def get_logs(self):
        logs = []

        for _ in range(10):
            entry = self.generate_log()
            logs.append(entry)

        return logs

    def generate_log(self):
        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")

        style_timestamp = '<span class="grey">'
        style_message = '<span>'
        style_origin = '<span>'
        style_end = '</span>'

        origin = random.sample(lorem_words, 1)[0]
        message = ' '.join(random.sample(lorem_words, 8))
        message = message[0].upper() + message[1:] + '.'

        type = random.random()

        if type <= 0.001:
            type = LogType.ERROR
            style_origin = '<span class="bold red">'
            style_message = '<span class="bold red">'
            message = '[ERROR] ' + message
        elif type <= 0.011:
            type = LogType.WARNING
            style_message = '<span class="bold yellow">'
            message = '[WARNING] ' + message

        return {
            'type':
                type,
            'text':
                f'{style_timestamp}{timestamp}{style_end} {style_origin}{origin:>15s}{style_end}: {style_message}{message}{style_end}'
        }


lorem = (
    "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
    "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
    "occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
    "mollit anim id est laborum.")

lorem_words = (
    "exercitationem",
    "perferendis",
    "perspiciatis",
    "laborum",
    "eveniet",
    "sunt",
    "iure",
    "nam",
    "nobis",
    "eum",
    "cum",
    "officiis",
    "excepturi",
    "odio",
    "consectetur",
    "quasi",
    "aut",
    "quisquam",
    "vel",
    "eligendi",
    "itaque",
    "non",
    "odit",
    "tempore",
    "quaerat",
    "dignissimos",
    "facilis",
    "neque",
    "nihil",
    "expedita",
    "vitae",
    "vero",
    "ipsum",
    "nisi",
    "animi",
    "cumque",
    "pariatur",
    "velit",
    "modi",
    "natus",
    "iusto",
    "eaque",
    "sequi",
    "illo",
    "sed",
    "ex",
    "et",
    "voluptatibus",
    "tempora",
    "veritatis",
    "ratione",
    "assumenda",
    "incidunt",
    "nostrum",
    "placeat",
    "aliquid",
    "fuga",
    "provident",
    "praesentium",
    "rem",
    "necessitatibus",
    "suscipit",
    "adipisci",
    "quidem",
    "possimus",
    "voluptas",
    "debitis",
    "sint",
    "accusantium",
    "unde",
    "sapiente",
    "voluptate",
    "qui",
    "aspernatur",
    "laudantium",
    "soluta",
    "amet",
    "quo",
    "aliquam",
    "saepe",
    "culpa",
    "libero",
    "ipsa",
    "dicta",
    "reiciendis",
    "nesciunt",
    "doloribus",
    "autem",
    "impedit",
    "minima",
    "maiores",
    "repudiandae",
    "ipsam",
    "obcaecati",
    "ullam",
    "enim",
    "totam",
    "delectus",
    "ducimus",
    "quis",
    "voluptates",
    "dolores",
    "molestiae",
    "harum",
    "dolorem",
    "quia",
    "voluptatem",
    "molestias",
    "magni",
    "distinctio",
    "omnis",
    "illum",
    "dolorum",
    "voluptatum",
    "ea",
    "quas",
    "quam",
    "corporis",
    "quae",
    "blanditiis",
    "atque",
    "deserunt",
    "laboriosam",
    "earum",
    "consequuntur",
    "hic",
    "cupiditate",
    "quibusdam",
    "accusamus",
    "ut",
    "rerum",
    "error",
    "minus",
    "eius",
    "ab",
    "ad",
    "nemo",
    "fugit",
    "officia",
    "at",
    "in",
    "id",
    "quos",
    "reprehenderit",
    "numquam",
    "iste",
    "fugiat",
    "sit",
    "inventore",
    "beatae",
    "repellendus",
    "magnam",
    "recusandae",
    "quod",
    "explicabo",
    "doloremque",
    "aperiam",
    "consequatur",
    "asperiores",
    "commodi",
    "optio",
    "dolor",
    "labore",
    "temporibus",
    "repellat",
    "veniam",
    "architecto",
    "est",
    "esse",
    "mollitia",
    "nulla",
    "a",
    "similique",
    "eos",
    "alias",
    "dolore",
    "tenetur",
    "deleniti",
    "porro",
    "facere",
    "maxime",
    "corrupti",
)

COMMON_WORDS = (
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipisicing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
)
