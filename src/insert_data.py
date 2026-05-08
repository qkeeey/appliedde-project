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

DATA_PATH = os.getenv("DATA_PATH", "/nifi/output")
BATCH_FILE = os.getenv("BATCH_FILE", "")


def load_dataframe(path: str, batch_file: str) -> pd.DataFrame:
    """Load a single batch CSV file from the NiFi output directory.

    Parameters
    ----------
    path : str
        Directory containing batch CSV files produced by NiFi.
    batch_file : str
        The specific batch filename to load (e.g., ``batch_0042.csv``).

    Returns
    -------
    pd.DataFrame
        The loaded DataFrame.

    Raises
    ------
    ValueError
        If *batch_file* is empty (no batch specified).
    FileNotFoundError
        If the batch file does not exist at the expected path.
    """
    if not batch_file:
        raise ValueError("BATCH_FILE environment variable is required.")

    batch_path = os.path.join(path, batch_file)
    df = pd.read_csv(batch_path)
    print(
        f"Loaded batch '{batch_file}' ({len(df)} rows)",
        flush=True,
    )
    return df


def _get_or_create_location(cur, key: tuple) -> int:
    """Return the location_id for the given key, inserting if necessary.

    Uses a select-first approach to avoid requiring a unique constraint
    on the locations table.

    Parameters
    ----------
    cur : psycopg2.cursor
        Active database cursor.
    key : tuple
        ``(neighbourhood_group, neighbourhood, latitude, longitude)``.

    Returns
    -------
    int
        The ``location_id`` for the given key.
    """
    cur.execute(
        """
        SELECT location_id FROM locations
        WHERE neighbourhood_group = %s
          AND neighbourhood = %s
          AND latitude = %s
          AND longitude = %s
        """,
        key,
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        INSERT INTO locations (neighbourhood_group, neighbourhood, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        RETURNING location_id
        """,
        key,
    )
    return cur.fetchone()[0]


def insert_data():
    """Load a single batch CSV into PostgreSQL via upsert.

    Reads the batch file specified by ``BATCH_FILE``, cleans the data,
    and upserts into all tables without truncating existing records.
    """
    conn = get_connection()
    cur = conn.cursor()

    print("Connected to PostgreSQL", flush=True)

    df = load_dataframe(DATA_PATH, BATCH_FILE)

    df = df.fillna({
        "name": "Unknown",
        "host_name": "Unknown",
        "reviews_per_month": 0
    })

    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce").dt.date
        df["last_review"] = df["last_review"].where(pd.notnull(df["last_review"]), None)

    # ── Hosts ────────────────────────────────────────────────────────
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

    # ── Locations ────────────────────────────────────────────────────
    location_map = {}

    for _, row in df.iterrows():
        key = (
            row["neighbourhood_group"],
            row["neighbourhood"],
            float(row["latitude"]),
            float(row["longitude"])
        )

        if key not in location_map:
            location_map[key] = _get_or_create_location(cur, key)

    conn.commit()
    print("Locations inserted", flush=True)

    # ── Listings ─────────────────────────────────────────────────────
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

    # ── Reviews ──────────────────────────────────────────────────────
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

    # ── Availability ─────────────────────────────────────────────────
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