FROM python:3.14-slim

WORKDIR /app

# Dependencies first, so Docker can cache this slow layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY pages/ pages/

RUN useradd --create-home appuser
USER appuser

EXPOSE 8501

# 0.0.0.0 so it is reachable from outside the container.
# headless = don't try to open a browser; usage stats off = don't phone home.
CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]