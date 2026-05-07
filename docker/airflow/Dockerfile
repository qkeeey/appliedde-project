FROM apache/airflow:2.8.1

USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         postgresql-client \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow

# Install dependencies required by the data ingestion and indexing scripts
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# We map the DAGs and src using volumes so we don't strictly need to copy them here,
# but we can set the PYTHONPATH so Airflow DAGs can easily import or use scripts.
ENV PYTHONPATH=/opt/airflow
