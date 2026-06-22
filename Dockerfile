FROM python:3.7-slim-buster

RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000


CMD ["python","app.py"]
