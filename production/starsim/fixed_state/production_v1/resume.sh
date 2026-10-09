#!/bin/sh
set -eu
AUDIT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export UV_CACHE_DIR="$AUDIT/uv-cache" NUMBA_CACHE_DIR="$AUDIT/numba-cache" MPLCONFIGDIR="$AUDIT/mpl"
export PYTHONDONTWRITEBYTECODE=1 STARSIM_SINGLE_RNG=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec uv run --offline --no-project --python /Users/elsehow/Projects/iclr-2026/.venv/bin/python --no-managed-python python "$AUDIT/resume.py"
