#!/bin/sh
set -eu
cd "$(dirname "$0")"
PROJECT=${SHERLOCK_PROJECT:-/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15}
exec /usr/bin/caffeinate -i "$PROJECT/.venv/bin/python" -B -u -m scripts.optional_v4_dagger "$@" --project "$PROJECT"
