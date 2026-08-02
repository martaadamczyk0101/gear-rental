# Built with repo root as the build context (not `backend/`) so this image can
# also COPY `seed.json`, which lives one level above `backend/` - see
# config.py's SEED_FILE (PROJECT_ROOT / "seed.json"). On Railway this means:
# leave the service's Root Directory unset and point RAILWAY_DOCKERFILE_PATH
# at backend/Dockerfile instead of scoping the whole service to backend/.
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY seed.json seed.json

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
