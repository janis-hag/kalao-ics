import random
import time
from datetime import datetime

import numpy as np
import pandas as pd

from PySide6.QtCore import QThread, Signal

from kalao.interfaces import fake_data

from guis.backends.abstract import AbstractBackend

from kalao.definitions.enums import LogType

import config

#TODO: replace with Streams enum?


class MainBackend(AbstractBackend):
    ttm_data = np.array([0, 0])

    streams_updated = Signal()
    streams = {}

    tiptilt_updated = Signal()
    tiptilt = {}

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update_streams(self, data):
        data.update({
            config.Streams.DM: {
                'updated': True,
                'data': fake_data.dm(),
            },
            config.FPS.BMC: {
                'max_stroke': {
                    'updated': True,
                    'value': 0.9
                }
            },
        })

        data.update({
            config.Streams.NUVU: {
                'updated':
                    True,
                'data':
                    fake_data.nuvu_frame(
                        tiptilt=self.ttm_data,
                        dmdisp=np.ma.getdata(data[config.Streams.DM]['data']))
            },
            config.Streams.FLI: {
                'updated':
                    True,
                'data':
                    fake_data.fli_frame(
                        tiptilt=self.ttm_data,
                        dmdisp=np.ma.getdata(data[config.Streams.DM]['data']))
            }
        })

        data.update({
            config.Streams.SLOPES: {
                'updated': True,
                'data': fake_data.slopes(data[config.Streams.NUVU]['data'])
            },
            config.Streams.FLUX: {
                'updated': True,
                'data': fake_data.flux(data[config.Streams.NUVU]['data'])
            }
        })

        data[config.FPS.SHWFS] = {}

        for k, v in fake_data.slopes_params(
                data[config.Streams.SLOPES]['data']).items():
            data[config.FPS.SHWFS].update({k: {'updated': True, 'value': v}})

        for k, v in fake_data.flux_params(
                data[config.Streams.FLUX]['data']).items():
            data[config.FPS.SHWFS].update({k: {'updated': True, 'value': v}})

        if data.get('aol1_mgainfact') is None:
            data.update({
                'aol1_mgainfact': {
                    'updated': True,
                    'data': np.ones((90, ))
                }
            })

    @AbstractBackend.timeit('tiptilt', 'tiptilt_updated')
    def update_tiptilt(self, data):
        self.ttm_data = fake_data.tiptilt(seed=self.ttm_data)

        data.update({
            config.Streams.TTM: {
                'updated': True,
                'data': self.ttm_data
            }
        })

    def get_plots_data(self, dt_start, dt_end, monitoring_keys,
                       telemetry_keys):
        timestamps = pd.date_range(dt_start, dt_end, 50)

        return {
            'monitoring':
                self._generate_plots_data(monitoring_keys, timestamps),
            'telemetry':
                self._generate_plots_data(telemetry_keys, timestamps),
        }

    def _generate_plots_data(self, keys, timestamps):
        data = {}
        for key in keys:
            data[key] = {
                timestamp: value
                for timestamp, value in zip(
                    timestamps, np.random.normal(0, 1, len(timestamps)))
            }

        df = pd.DataFrame(data, columns=keys)

        return df


class DMChannelsBackend(AbstractBackend):
    streams_updated = Signal()
    streams = {}

    def __init__(self, dm_number):
        super().__init__()

        self.dm_number = dm_number

    @AbstractBackend.timeit('streams', 'streams_updated')
    def update(self, data):
        if self.dm_number == 1:
            dm_data = fake_data.dm([0])

            for i in range(0, 12):
                channel = f'dm{self.dm_number:02d}disp{i:02d}'

                channel_data = fake_data.dm()
                dm_data += channel_data

                data.update({channel: {'updated': True, 'data': channel_data}})

            data.update({
                f'dm{self.dm_number:02d}disp': {
                    'updated': True,
                    'data': dm_data
                }
            })

        else:
            dm_data = np.zeros((2, ))

            for i in range(0, 12):
                channel = f'dm{self.dm_number:02d}disp{i:02d}'

                channel_data = fake_data.tiptilt()
                dm_data += channel_data

                data.update({
                    channel: {
                        'updated': True,
                        'data': channel_data.reshape((1, 2))
                    }
                })

            data.update({
                f'dm{self.dm_number:02d}disp': {
                    'updated': True,
                    'data': dm_data.reshape((1, 2))
                }
            })

    def reset_dm(self, dm_number):
        print(f'Resetted DM {dm_number} (virtually)')

    def reset_channel(self, dm_number, channel):
        print(f'Resetted channel {channel} of DM {dm_number} (virtually)')


class LogsThread(QThread):
    new_log = Signal(object)

    def run(self):
        for _ in range(config.GUI.initial_logs_entries):
            entry = self.generate_log()
            entry['text'] = '<span class="init">' + entry['text'] + '<span>'
            self.new_log.emit(entry)

        while not self.isInterruptionRequested():
            entry = self.generate_log()
            self.new_log.emit(entry)

            time.sleep(0.1)

    def generate_log(self):
        type = random.random()

        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")

        style_timestamp = '<span class="grey">'
        style_message = '<span>'
        style_origin = '<span>'
        style_end = '</span>'

        origin = random.sample(lorem_words, 1)[0]
        message = ' '.join(random.sample(lorem_words, 8))
        message = message[0].upper() + message[1:] + '.'

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
