import os
import json
import time
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
from elasticsearch import Elasticsearch, helpers


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airbnb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "airbnb_listings")

MAPPING_PATH = "/app/airbnb_mapping.json"


def get_postgres_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_elasticsearch_client():
    return Elasticsearch(
        ELASTICSEARCH_HOST,
        request_timeout=60,
        retry_on_timeout=True,
        max_retries=5
    )


def load_mapping():
    with open(MAPPING_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def recreate_index(es):
    mapping = load_mapping()

    if es.indices.exists(index=ELASTICSEARCH_INDEX):
        print(f"Deleting existing index: {ELASTICSEARCH_INDEX}", flush=True)
        es.indices.delete(index=ELASTICSEARCH_INDEX)

    print(f"Creating index: {ELASTICSEARCH_INDEX}", flush=True)
    es.indices.create(index=ELASTICSEARCH_INDEX, body=mapping)


def price_category(price):
    if price is None:
        return "unknown"
    if price <= 75:
        return "low"
    if price <= 175:
        return "medium"
    if price <= 350:
        return "high"
    return "luxury"


def availability_category(days):
    if days is None:
        return "unknown"
    if days == 0:
        return "unavailable"
    if days <= 90:
        return "low_availability"
    if days <= 250:
        return "medium_availability"
    return "high_availability"


def fetch_airbnb_documents():
    query = """
        SELECT
            l.listing_id,
            l.name,
            l.room_type,
            l.price,
            l.minimum_nights,

            h.host_id,
            h.host_name,
            h.calculated_host_listings_count,

            loc.neighbourhood_group,
            loc.neighbourhood,
            loc.latitude,
            loc.longitude,

            r.number_of_reviews,
            r.last_review,
            r.reviews_per_month,

            a.availability_365

        FROM listings l
        JOIN hosts h
            ON l.host_id = h.host_id
        JOIN locations loc
            ON l.location_id = loc.location_id
        LEFT JOIN reviews r
            ON l.listing_id = r.listing_id
        LEFT JOIN availability a
            ON l.listing_id = a.listing_id
        WHERE l.price IS NOT NULL
          AND l.price >= 0;
    """

    conn = get_postgres_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    print(f"Fetched {len(rows)} rows from PostgreSQL.", flush=True)
    return rows


def convert_row_to_document(row):
    last_review = row["last_review"]
    if last_review is not None:
        last_review = last_review.isoformat()

    price = float(row["price"]) if row["price"] is not None else None
    availability_365 = int(row["availability_365"]) if row["availability_365"] is not None else None

    return {
        "listing_id": int(row["listing_id"]),
        "name": row["name"],
        "host_id": int(row["host_id"]),
        "host_name": row["host_name"],
        "calculated_host_listings_count": int(row["calculated_host_listings_count"]),

        "neighbourhood_group": row["neighbourhood_group"],
        "neighbourhood": row["neighbourhood"],
        "location": {
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"])
        },

        "room_type": row["room_type"],
        "price": price,
        "price_category": price_category(price),
        "minimum_nights": int(row["minimum_nights"]),

        "number_of_reviews": int(row["number_of_reviews"]) if row["number_of_reviews"] is not None else 0,
        "last_review": last_review,
        "reviews_per_month": float(row["reviews_per_month"]) if row["reviews_per_month"] is not None else 0.0,

        "availability_365": availability_365,
        "availability_category": availability_category(availability_365),

        "indexed_at": datetime.now(timezone.utc).isoformat()
    }


def generate_bulk_actions(rows):
    for row in rows:
        document = convert_row_to_document(row)

        yield {
            "_index": ELASTICSEARCH_INDEX,
            "_id": document["listing_id"],
            "_source": document
        }


def index_documents(es, rows):
    print("Indexing documents into Elasticsearch...", flush=True)

    success_count, errors = helpers.bulk(
        es,
        generate_bulk_actions(rows),
        chunk_size=1000,
        request_timeout=120,
        raise_on_error=False
    )

    print(f"Successfully indexed documents: {success_count}", flush=True)

    if errors:
        print(f"Indexing errors: {len(errors)}", flush=True)
        print(errors[:5], flush=True)


def print_index_summary(es):
    es.indices.refresh(index=ELASTICSEARCH_INDEX)

    count_response = es.count(index=ELASTICSEARCH_INDEX)
    print(f"Elasticsearch document count: {count_response['count']}", flush=True)

    agg_response = es.search(
        index=ELASTICSEARCH_INDEX,
        size=0,
        aggs={
            "listings_by_borough": {
                "terms": {
                    "field": "neighbourhood_group",
                    "size": 10
                }
            },
            "avg_price": {
                "avg": {
                    "field": "price"
                }
            }
        }
    )

    print("Listings by borough:", flush=True)
    for bucket in agg_response["aggregations"]["listings_by_borough"]["buckets"]:
        print(f"- {bucket['key']}: {bucket['doc_count']}", flush=True)

    print(f"Average price: {agg_response['aggregations']['avg_price']['value']:.2f}", flush=True)


def main():
    es = get_elasticsearch_client()

    recreate_index(es)

    rows = fetch_airbnb_documents()
    index_documents(es, rows)

    print_index_summary(es)
    print("Elasticsearch indexing completed successfully.", flush=True)


if __name__ == "__main__":
    main()
