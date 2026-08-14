FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DESIGN_FLOW_API_HOST=0.0.0.0 \
    DESIGN_FLOW_API_PORT=8080 \
    DESIGN_FLOW_PROJECT_ROOT=/data

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN python -m pip install --no-cache-dir .

VOLUME ["/data"]
EXPOSE 8080
CMD ["python", "-m", "design_flow_action_api"]
