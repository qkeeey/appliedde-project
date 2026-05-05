FROM python:3.10-slim

WORKDIR /app

COPY src/es_indexer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/es_indexer/index_airbnb.py .
COPY docker/elasticsearch/airbnb_mapping.json /app/airbnb_mapping.json

CMD ["python", "-u", "index_airbnb.py"]