FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system mke \
    && useradd --system --gid mke --create-home --home-dir /home/mke mke

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=mke:mke . .
RUN chmod +x /app/deploy/entrypoint.sh \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R mke:mke /app/staticfiles /app/media

USER mke
EXPOSE 8000
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "making_life_easier.asgi:application"]
