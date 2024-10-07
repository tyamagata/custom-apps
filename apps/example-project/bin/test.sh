#!/bin/sh
# Usage: bin/test
set -x
set -e

cd "$(dirname "$0")/.."
python -B -m pytest -p no:cacheprovider
