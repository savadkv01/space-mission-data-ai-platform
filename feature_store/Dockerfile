FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY feature_store/requirements.txt /app/feature_store/requirements.txt
RUN pip install --no-cache-dir -r /app/feature_store/requirements.txt

COPY feature_store /app/feature_store

EXPOSE 6566
CMD ["python", "-m", "feature_store.entrypoint"]
