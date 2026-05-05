# NYC Airbnb Applied Data Engineering Pipeline

This project implements a containerized end-to-end data engineering pipeline for the New York City Airbnb Open Data dataset.

The current pipeline loads Airbnb listing data into PostgreSQL, indexes denormalized listing documents into Elasticsearch, and visualizes the data through Kibana dashboards.

## Architecture

CSV Dataset
    ↓
Data Loader Container
    ↓
PostgreSQL
    ↓
Elasticsearch Indexer Container
    ↓
Elasticsearch
    ↓
Kibana Dashboard

## Services

- postgres: relational storage for normalized Airbnb data.
- data_loader: Python container that loads the CSV dataset into PostgreSQL.
- elasticsearch: search and analytics engine.
- es_indexer: Python container that reads PostgreSQL data and indexes it into Elasticsearch.
- kibana: dashboard and visualization layer.

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

## Verify PostgreSQL to Elasticsearch Indexing

After the services start, check Elasticsearch:

    curl http://localhost:9200/_cluster/health?pretty
    curl http://localhost:9200/_cat/indices?v
    curl http://localhost:9200/airbnb_listings/_count?pretty

Expected document count:

    48895

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
    ├── docker
    │   ├── elasticsearch
    │   │   └── airbnb_mapping.json
    │   ├── kibana
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
    │   │   ├── Dockerfile
    │   │   ├── index_airbnb.py
    │   │   └── requirements.txt
    │   ├── Dockerfile
    │   └── insert_data.py
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

- The current ingestion step loads a static CSV file rather than a live external data stream.
- Kibana dashboards are restored from exported saved objects.
- The current version uses a single-node Elasticsearch setup suitable for local demonstration.
- The current pipeline is optimized for local execution on a student laptop, not production deployment.
- Apache Airflow and Apache NiFi integration are planned as separate pipeline layers.

## Team Members

- Nikolas Leka
- Kuanysh Otegen
- Emre Demirci
- Rafi Putra Abdurrahman
