#!/usr/bin/env bash

set -euxo pipefail

uv sync --dev --all-groups

exec uv run watchmedo auto-restart --directory src --recursive -- python -m src
