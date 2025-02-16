FROM python:3.12-slim

ARG UV_VERSION=0.6.0
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /tmp

SHELL [ "/bin/bash", "-euxo", "pipefail", "-c" ]
RUN apt-get update && apt-get install -y --no-install-recommends curl

ADD https://astral.sh/uv/${UV_VERSION}/install.sh install-uv.sh

RUN chmod +x install-uv.sh && ./install-uv.sh

WORKDIR /app

ENTRYPOINT [ "/app/docker-entrypoint.dev.sh" ]
