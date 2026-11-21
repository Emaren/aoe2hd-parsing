FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH="/app" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Deliberately copy only files required by the running API. Historical
# database URLs, Firebase service keys, SQL dumps, scripts, and repository
# metadata cannot enter the runtime image even if they remain in Git.
COPY requirements.txt /app/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client libpq-dev gcc python3-dev && \
    python -m pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get purge -y --auto-remove gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY app.py config.py /app/
COPY db/*.py /app/db/
COPY db/models/*.py /app/db/models/
COPY routes/*.py /app/routes/

EXPOSE 8000
# No unreviewed Alembic migration or schema mutation on process start.
ENTRYPOINT ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port 8000"]
