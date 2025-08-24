FROM python:3.12.0-slim-bullseye AS build

RUN apt-get update \
    && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
# only install dependencies
COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --no-config --no-dev --frozen --no-install-project

# now add the project to the venv
COPY ./src /app/src
RUN uv sync --no-dev --frozen


FROM python:3.12.0-slim-bullseye AS app

RUN useradd --home /app app
RUN mkdir -p /app && chown -R app:app /app
USER app

# This "enables" the virtualenv that we install in the build stage:
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=build /app/.venv /app/.venv
COPY ./src /app/src

WORKDIR /app
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "ai_ethics_assistant.cmds.server:app"]