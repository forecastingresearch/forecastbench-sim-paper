#!/bin/sh
set -eu
AUDIT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export UV_CACHE_DIR="$AUDIT/uv-cache" MPLCONFIGDIR="$AUDIT/mpl" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
exec uv run --offline --no-project --python /Users/elsehow/Projects/iclr-score-refresh/venv/bin/python --no-managed-python python "$AUDIT/rescore.py"
