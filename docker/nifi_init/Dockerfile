FROM python:3.11-slim

RUN pip install --no-cache-dir requests urllib3

COPY src/nifi/init_nifi_flow.py /app/init_nifi_flow.py

CMD ["python", "/app/init_nifi_flow.py"]
