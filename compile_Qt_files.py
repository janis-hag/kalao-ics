#!/usr/bin/env python

import subprocess
from pathlib import Path

output_folder = Path(__file__).absolute().parent / 'compiled'

output_folder.mkdir(parents=True, exist_ok=True)


def generate_file(file: Path) -> None:
    if file.suffix == '.ui':
        output = output_folder / f'ui_{file.stem}.py'

        command = [
            'pyside6-uic', '--rc-prefix', '--from-imports',
            str(file), '--output',
            str(output)
        ]
    elif file.suffix == '.qrc':
        output = output_folder / f'rc_{file.stem}.py'

        command = ['pyside6-rcc', str(file), '--output', f'{output}']
    else:
        raise ValueError(f'Unsupported file extension "{file.suffix}"')

    if not output.exists() or output.stat().st_mtime < file.stat().st_mtime:
        print(f'Running {" ".join(command)}')
        subprocess.run(command, capture_output=True)
    else:
        print(f'Skipping {file}')


for ui in Path('assets/uis').glob('*.ui'):
    generate_file(ui)

generate_file(Path('assets/assets.qrc'))
