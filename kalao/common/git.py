import subprocess
from pathlib import Path


def get_version(repository: Path) -> str:
    return subprocess.check_output([
        'git', 'describe', '--abbrev=7', '--dirty', '--always', '--tags'
    ], cwd=repository).decode().strip()
