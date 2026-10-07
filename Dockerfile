FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /tmp

SHELL [ "/bin/bash", "-euxo", "pipefail", "-c" ]
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends curl

COPY --from=astral/uv:0.12 /uv /uvx /usr/local/bin/

WORKDIR /app

ENTRYPOINT [ "/app/docker-entrypoint.dev.sh" ]
