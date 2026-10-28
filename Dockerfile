# ---------- base: dependencies + trained model ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN python -m app.model

# ---------- test: run the unit tests (the build fails if a test fails) ----------
FROM base AS test
COPY requirements-dev.txt pytest.ini ./
COPY tests/ ./tests/
RUN pip install --no-cache-dir -r requirements-dev.txt && python -m pytest -q

# ---------- runtime: production image ----------
FROM base AS runtime
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.app:app"]
