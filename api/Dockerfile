FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY api/pyproject.toml api/README.md ./
RUN pip install --upgrade pip && pip install .

COPY api/alembic.ini ./
COPY api/alembic ./alembic
COPY api/app ./app
COPY api/models ./models
RUN chown -R app:app /app/models

COPY training /training

COPY api/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
