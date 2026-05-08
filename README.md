# NYC Airbnb Applied Data Engineering Pipeline

This project implements a containerized end-to-end data engineering pipeline for the New York City Airbnb Open Data dataset. 

Apache NiFi simulates real-time data ingestion by streaming the CSV dataset in batches with time-intervals. Each batch triggers an Apache Airflow DAG run via REST API, which upserts the data into PostgreSQL and incrementally indexes it into Elasticsearch. Kibana provides real-time visualization as data streams in.

## Architecture

    CSV Dataset
        ↓
    NiFi (stream_csv.py via ExecuteStreamCommand)
        ↓  writes 500-row batch files + triggers Airflow REST API
    Airflow DAG (per-batch, event-driven)
        ↓  insert_data.py (upsert, no truncate)
    PostgreSQL
    ↓
    Elasticsearch Indexer Container
    ↓
    Elasticsearch
        ↓
    Kibana Dashboard

## Services

- **nifi**: Apache NiFi 2.8.0, runs the streaming flow that chunks the CSV and writes batch files.
- **nifi-init**: one-shot container that programmatically builds the NiFi flow via the REST API.
- **airflow-webserver**: Airflow 2.8.1 web UI and REST API endpoint (receives triggers from NiFi).
- **airflow-scheduler**: executes DAG runs sequentially (`max_active_runs=1`).
- **airflow-init**: one-shot container that initializes the Airflow database and admin user.
- **postgres**: PostgreSQL 15, stores normalized Airbnb data and the Airflow metadata database.
- **elasticsearch**: Elasticsearch 8.13.2, stores denormalized listing documents.
- **kibana**: Kibana 8.13.2, dashboard and visualization layer.
- **kibana-setup**: one-shot container that creates the Kibana data view.

## Requirements

- Docker
- Docker Compose

No Python, PostgreSQL, Elasticsearch, or Kibana installation is required on the host machine.

## Setup

Clone the repository:

    git clone https://github.com/qkeeey/appliedde-project.git
    cd appliedde-project

Create the environment file:

    cp .env.example .env

Start the full pipeline:

    docker compose down -v
    docker compose up --build

## Verify Pipeline

The pipeline streams data incrementally. The document count grows from 0 to 48895 over approximately 10 minutes (98 batches x 3-second intervals + processing time).

Check Elasticsearch:

    curl http://localhost:9200/_cluster/health?pretty
    curl http://localhost:9200/_cat/indices?v
    curl http://localhost:9200/airbnb_listings/_count?pretty

Final expected document count:

    48895

Check Airflow DAG runs (should reach 98 successful runs):

    http://localhost:8080  (admin / admin)

## Kibana

Open Kibana:

    http://localhost:5601

The Kibana saved objects export is stored at:

    docs/kibana/airbnb_kibana_saved_objects.ndjson

To restore the dashboard manually:

1. Open Kibana.
2. Go to Stack Management.
3. Go to Saved Objects.
4. Click Import.
5. Select docs/kibana/airbnb_kibana_saved_objects.ndjson.
6. Enable overwrite if prompted.
7. Open Analytics → Dashboard.

Dashboard name:

    NYC Airbnb Analytics Dashboard

## Main Dashboard Visualizations

The dashboard includes:

- listings by NYC borough
- top neighbourhoods by listing count
- price distribution
- average price by room type
- room type breakdown
- listing availability analysis
- geospatial Airbnb listing map

## Repository Structure

    .
    ├── dags
    │   └── airbnb_pipeline.py          # Airflow DAG (event-driven, per-batch)
    ├── docker
    │   ├── airflow
    │   │   └── Dockerfile
    │   ├── elasticsearch
    │   │   └── airbnb_mapping.json
    │   ├── kibana
    │   ├── nifi
    │   │   └── Dockerfile              # NiFi with python3-requests
    │   ├── nifi_init
    │   │   └── Dockerfile              # Flow builder container
    │   └── postgres
    │       └── Dockerfile
    ├── docs
    │   └── kibana
    │       └── airbnb_kibana_saved_objects.ndjson
    ├── sql
    │   └── schema.sql
    ├── src
    │   ├── data
    │   │   └── AB_NYC_2019.csv
    │   ├── es_indexer
    │   │   └── index_airbnb.py          # Incremental ES indexer
    │   ├── nifi
    │   │   ├── init_nifi_flow.py        # Programmatic NiFi flow builder
    │   │   └── stream_csv.py           # CSV chunker + Airflow trigger
    │   └── insert_data.py              # Per-batch upsert into PostgreSQL
    ├── docker-compose.yml
    ├── .env.example
    ├── .gitignore
    └── README.md

## Elasticsearch Index

The Elasticsearch index is named:

    airbnb_listings

It stores one denormalized document per Airbnb listing. Each document combines listing, host, location, review, and availability fields from PostgreSQL.

Important mapped fields include:

- listing_id: unique listing identifier
- name: listing title
- host_id: host identifier
- host_name: host name
- neighbourhood_group: NYC borough
- neighbourhood: neighbourhood name
- location: geo_point field for maps
- room_type: Airbnb room type
- price: listing price
- price_category: derived price bucket
- minimum_nights: minimum stay requirement
- number_of_reviews: review count
- reviews_per_month: monthly review rate
- availability_365: yearly availability
- availability_category: derived availability bucket
- indexed_at: indexing timestamp

## Useful Commands

View running containers:

    docker ps

View all containers:

    docker ps -a

View logs for the Elasticsearch indexer:

    docker compose logs es_indexer

View logs continuously:

    docker compose logs -f

Stop all services:

    docker compose down

Stop all services and remove volumes:

    docker compose down -v

Rebuild everything from scratch:

    docker compose down -v
    docker compose up --build

## Example Elasticsearch Queries

Check index count:

    curl http://localhost:9200/airbnb_listings/_count?pretty

Search listings in Harlem:

    curl -X GET "http://localhost:9200/airbnb_listings/_search?pretty" -H "Content-Type: application/json" -d '{"size":3,"_source":["listing_id","name","neighbourhood_group","neighbourhood","room_type","price"],"query":{"match":{"neighbourhood":"Harlem"}}}'

Aggregate listings by borough:

    curl -X GET "http://localhost:9200/airbnb_listings/_search?pretty" -H "Content-Type: application/json" -d '{"size":0,"aggs":{"listings_by_borough":{"terms":{"field":"neighbourhood_group","size":10}}}}'

Average price by room type:

    curl -X GET "http://localhost:9200/airbnb_listings/_search?pretty" -H "Content-Type: application/json" -d '{"size":0,"aggs":{"room_types":{"terms":{"field":"room_type","size":10},"aggs":{"average_price":{"avg":{"field":"price"}}}}}}'

## Known Limitations

- The data source is a static CSV file; NiFi simulates real-time ingestion by chunking and throttling.
- Kibana dashboards are restored from exported saved objects.
- Single-node Elasticsearch setup suitable for local demonstration.
- The `locations` table uses a select-first insert pattern, requiring `max_active_runs=1` to prevent race conditions.
- The pipeline is optimized for local execution on a student laptop, not production deployment.

## Team Members

- Nikolas Leka
- Kuanysh Otegen
- Emre Demirci
- Rafi Putra Abdurrahman
