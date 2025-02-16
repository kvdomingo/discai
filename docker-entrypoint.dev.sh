#!/usr/bin/env bash

set -euxo pipefail

uv sync
uv run alembic upgrade head

exec uv run watchmedo auto-restart --directory src --recursive -- python -m src
