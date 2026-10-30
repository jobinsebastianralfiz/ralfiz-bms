# Notes app frontend (noetsa_frontend/, React + Vite): built here so the Python
# image needs no Node. Its dist/ is collected as /static/noetsa/ (config/settings.py).
FROM node:22-slim AS notes-frontend
WORKDIR /build
COPY noetsa_frontend/package.json noetsa_frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY noetsa_frontend/ ./
RUN npm run build

FROM python:3.12-slim

# System deps for dlib (face_recognition), weasyprint, and psycopg2.
# fonts-noto-core gives Notes PDF exports correct Malayalam/Hindi shaping.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libpng-dev \
    libjpeg-dev \
    pkg-config \
    libpango1.0-dev \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    libcairo2-dev \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir "setuptools<81" && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=notes-frontend /build/dist /app/noetsa_frontend/dist

# Railway sets PORT env var
CMD python manage.py collectstatic --noinput && \
    python manage.py migrate && \
    python manage.py createcachetable && \
    (python manage.py import_labs || echo "import_labs failed; Academy content not updated") && \
    gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --timeout 120
