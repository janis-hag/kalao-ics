#!/bin/bash

set -euo pipefail

# Ensure we are in the kalao-ics directory
pushd "$(dirname -- "$(readlink -f -- "$0")")/../.." > /dev/null

PYTHONUNBUFFERED=1 PYTHONPATH=$(pwd) python kalao/guis/alignment.py --simulation

popd > /dev/null
