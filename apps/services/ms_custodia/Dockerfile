FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/apps/services:/app/apps/web
WORKDIR /app
COPY apps/services/requirements.txt apps/services/requirements-storage.txt /deps/
COPY apps/web/requirements.txt /deps/web.txt
COPY apps/services/requirements-verified.txt /deps/constraints.txt
RUN pip install --no-cache-dir -c /deps/constraints.txt -r /deps/requirements-storage.txt -r /deps/web.txt && useradd --uid 10001 --create-home redhouse
COPY apps/services/redhouse /app/apps/services/redhouse
COPY apps/services/run.py apps/services/worker.py /app/apps/services/
COPY deployment/container.py deployment/healthcheck.py /app/deployment/
COPY apps/services/ms_custodia /app/apps/services/ms_custodia
USER 10001:10001
ENTRYPOINT ["python", "/app/deployment/container.py", "custodia"]
