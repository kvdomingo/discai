FROM python:3.12-slim AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

FROM base AS build

ARG UV_VERSION=0.6.0
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

SHELL [ "/bin/bash", "-euxo", "pipefail", "-c" ]
RUN apt-get update && apt-get install -y --no-install-recommends curl

ADD https://astral.sh/uv/${UV_VERSION}/install.sh install-uv.sh

COPY pyproject.toml uv.lock ./

RUN chmod +x install-uv.sh && \
    ./install-uv.sh && \
    uv venv .venv && \
    uv sync --frozen --no-dev

FROM base

WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY . .

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
