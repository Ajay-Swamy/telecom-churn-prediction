FROM python:3.14-slim

WORKDIR /app

# Install dependencies BEFORE copying the code. Docker caches this layer, so
# rebuilds after a code change skip the slow install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the API needs. train.py, notebooks and data stay out of the image.
COPY backend/ backend/
COPY model/churn_pipeline.joblib model/churn_pipeline.joblib
COPY model/model_metadata.json model/model_metadata.json

# Run as a normal user instead of root (a basic security habit).
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# 0.0.0.0 = listen on all network interfaces. The default 127.0.0.1 would only
# accept connections from INSIDE the container, so your browser could never reach it.
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]