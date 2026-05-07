import os
import time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "airbnb"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )


def insert_data(file_path="/opt/airflow/src/data/AB_NYC_2019.csv"):
    conn = get_connection()
    cur = conn.cursor()

    print("Connected to PostgreSQL", flush=True)

    df = pd.read_csv(file_path)

    df = df.fillna({
        "name": "Unknown",
        "host_name": "Unknown",
        "reviews_per_month": 0
    })

    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce").dt.date
        df["last_review"] = df["last_review"].where(pd.notnull(df["last_review"]), None)

    cur.execute("""
        TRUNCATE TABLE availability, reviews, listings, locations, hosts
        RESTART IDENTITY CASCADE;
    """)
    conn.commit()

    hosts = df[[
        "host_id",
        "host_name",
        "calculated_host_listings_count"
    ]].drop_duplicates(subset=["host_id"])

    host_rows = [
        (
            int(row["host_id"]),
            row["host_name"],
            int(row["calculated_host_listings_count"])
        )
        for _, row in hosts.iterrows()
    ]

    execute_values(
        cur,
        """
        INSERT INTO hosts (
            host_id,
            host_name,
            calculated_host_listings_count
        )
        VALUES %s
        ON CONFLICT (host_id) DO NOTHING
        """,
        host_rows
    )

    conn.commit()
    print("Hosts inserted", flush=True)

    location_map = {}

    for _, row in df.iterrows():
        key = (
            row["neighbourhood_group"],
            row["neighbourhood"],
            float(row["latitude"]),
            float(row["longitude"])
        )

        if key not in location_map:
            cur.execute("""
                INSERT INTO locations (
                    neighbourhood_group,
                    neighbourhood,
                    latitude,
                    longitude
                )
                VALUES (%s, %s, %s, %s)
                RETURNING location_id
            """, key)

            location_map[key] = cur.fetchone()[0]

    conn.commit()
    print("Locations inserted", flush=True)

    listing_rows = []

    for _, row in df.iterrows():
        key = (
            row["neighbourhood_group"],
            row["neighbourhood"],
            float(row["latitude"]),
            float(row["longitude"])
        )

        listing_rows.append((
            int(row["id"]),
            row["name"],
            int(row["host_id"]),
            location_map[key],
            row["room_type"],
            float(row["price"]),
            int(row["minimum_nights"])
        ))

    execute_values(
        cur,
        """
        INSERT INTO listings (
            listing_id,
            name,
            host_id,
            location_id,
            room_type,
            price,
            minimum_nights
        )
        VALUES %s
        ON CONFLICT (listing_id) DO NOTHING
        """,
        listing_rows
    )

    conn.commit()
    print("Listings inserted", flush=True)

    review_rows = [
        (
            int(row["id"]),
            int(row["number_of_reviews"]),
            row["last_review"] if "last_review" in df.columns else None,
            float(row["reviews_per_month"])
        )
        for _, row in df.iterrows()
    ]

    execute_values(
        cur,
        """
        INSERT INTO reviews (
            listing_id,
            number_of_reviews,
            last_review,
            reviews_per_month
        )
        VALUES %s
        ON CONFLICT (listing_id) DO NOTHING
        """,
        review_rows
    )

    conn.commit()
    print("Reviews inserted", flush=True)

    availability_rows = [
        (
            int(row["id"]),
            int(row["availability_365"])
        )
        for _, row in df.iterrows()
    ]

    execute_values(
        cur,
        """
        INSERT INTO availability (
            listing_id,
            availability_365
        )
        VALUES %s
        ON CONFLICT (listing_id) DO NOTHING
        """,
        availability_rows
    )

    conn.commit()
    print("Availability inserted", flush=True)

    cur.execute("SELECT COUNT(*) FROM listings;")
    listing_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM hosts;")
    host_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM locations;")
    location_count = cur.fetchone()[0]

    print(f"Listings count: {listing_count}", flush=True)
    print(f"Hosts count: {host_count}", flush=True)
    print(f"Locations count: {location_count}", flush=True)
    print("Data loading completed successfully", flush=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    insert_data()