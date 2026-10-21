FROM python:3.13-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 REGISTRY_DIR=/srv/registry
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY app ./app
# Local image bakes the current champion; on Cloud Run set MODEL_GCS_URI to load from GCS instead.
COPY registry ./registry
RUN useradd --system --uid 10001 appuser && chown -R appuser /srv
USER 10001
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/health')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
