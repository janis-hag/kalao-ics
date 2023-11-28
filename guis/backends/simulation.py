import random
import time
from datetime import datetime

import numpy as np

from PySide2.QtCore import QThread, Signal

from kalao.interfaces import fake_data

from guis.backends.generic import GenericBackend

from kalao.definitions.enums import LogType

import config

#TODO: replace with Streams enum?


class SimulationBackend(GenericBackend):
    ttm_data = np.array([0, 0])

    def update(self):
        self.ttm_data = fake_data.tiptilt(seed=self.ttm_data)

        self.data.update({
            'dm01disp': {
                'data': fake_data.dm(),
                'max_stroke': 0.9
            },
            'dm02disp': {
                'data': self.ttm_data
            }
        })

        self.data.update({
            'nuvu_stream': {
                'data':
                    fake_data.nuvu_frame(
                        tiptilt=self.data['dm02disp']['data'],
                        dmdisp=np.ma.getdata(self.data['dm01disp']['data']))
            },
            'fli_stream': {
                'data':
                    fake_data.fli_frame(
                        tiptilt=self.data['dm02disp']['data'],
                        dmdisp=np.ma.getdata(self.data['dm01disp']['data']))
            }
        })

        self.data.update({
            'shwfs_slopes': {
                'data': fake_data.slopes(self.data['nuvu_stream']['data'])
            },
            'shwfs_slopes_flux': {
                'data': fake_data.flux(self.data['nuvu_stream']['data'])
            }
        })

        self.data['shwfs_slopes'].update(
            fake_data.slopes_params(self.data['shwfs_slopes']['data']))
        self.data['shwfs_slopes_flux'].update(
            fake_data.flux_params(self.data['shwfs_slopes_flux']['data']))

        self.updated.emit()


class SimulationLogsThread(QThread):
    log = Signal(object)

    def run(self):
        for _ in range(config.GUI.initial_logs_entries):
            self.generate_log()

        while not self.isInterruptionRequested():
            self.generate_log()

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

        self.log.emit({
            'type':
                type,
            'text':
                f'{style_timestamp}{timestamp}{style_end} {style_origin}{origin:>15s}{style_end}: {style_message}{message}{style_end}'
        })


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
