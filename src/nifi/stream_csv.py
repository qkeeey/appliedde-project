"""stream_csv.py -- Split and stream the Airbnb CSV into batch files.

Called by the NiFi ExecuteStreamCommand processor to simulate real-time
data ingestion. Reads the source CSV, splits it into 500-row chunks,
and writes each chunk to the output directory with a 3-second delay
between batches.

After each batch is written, the script triggers an Airflow DAG run
via the REST API so that the batch is ingested incrementally.
"""

import os
import sys
import time
import csv

import requests

INPUT_FILE = os.getenv("NIFI_INPUT_FILE", "/nifi/input/AB_NYC_2019.csv")
OUTPUT_DIR = os.getenv("NIFI_OUTPUT_DIR", "/nifi/output")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
DELAY_SEC = float(os.getenv("DELAY_SEC", "3"))

AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://airflow-webserver:8080")
AIRFLOW_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "airbnb_pipeline")
AIRFLOW_USER = os.getenv("AIRFLOW_USER", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")


def _wait_for_airflow() -> None:
    """Block until the Airflow REST API is reachable.

    Called once before the first batch trigger to avoid losing early
    batches during the startup race (NiFi starts streaming before
    Airflow's webserver is ready).
    """
    url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{AIRFLOW_DAG_ID}"
    for attempt in range(1, 31):
        try:
            resp = requests.get(
                url, auth=(AIRFLOW_USER, AIRFLOW_PASSWORD), timeout=5,
            )
            if resp.status_code < 500:
                print(
                    f"Airflow API reachable (attempt {attempt}).",
                    flush=True,
                )
                return
        except requests.exceptions.RequestException:
            pass
        print(
            f"Waiting for Airflow API... (attempt {attempt}/30)",
            flush=True,
        )
        time.sleep(2)
    print("WARNING: Airflow API not reachable after 60s, proceeding anyway.", flush=True)


def _trigger_airflow(batch_file: str, batch_idx: int) -> None:
    """Trigger an Airflow DAG run for the given batch file.

    Retries up to 3 times with a 2-second delay on failure.

    Parameters
    ----------
    batch_file : str
        Filename of the batch CSV (e.g., ``batch_0042.csv``).
    batch_idx : int
        Zero-based batch sequence number.
    """
    url = f"{AIRFLOW_BASE_URL}/api/v1/dags/{AIRFLOW_DAG_ID}/dagRuns"
    payload = {
        "conf": {"batch_file": batch_file},
        "dag_run_id": f"nifi_batch_{batch_idx:04d}_{int(time.time())}",
    }
    for attempt in range(1, 4):
        try:
            resp = requests.post(
                url,
                json=payload,
                auth=(AIRFLOW_USER, AIRFLOW_PASSWORD),
                timeout=10,
            )
            if resp.status_code in (200, 201):
                print(
                    f"[batch {batch_idx:04d}] Triggered Airflow DAG run",
                    flush=True,
                )
                return
            print(
                f"[batch {batch_idx:04d}] Airflow returned "
                f"{resp.status_code} (attempt {attempt}/3)",
                flush=True,
            )
        except requests.exceptions.RequestException as exc:
            print(
                f"[batch {batch_idx:04d}] Trigger failed: {exc} "
                f"(attempt {attempt}/3)",
                flush=True,
            )
        time.sleep(2)


def stream_csv() -> None:
    """Read the source CSV and write numbered batch files with delays.

    Each batch file retains the original CSV header and contains at most
    ``CHUNK_SIZE`` data rows. A ``DELAY_SEC`` pause is inserted between
    successive writes to simulate real-time data arrival. After each
    write, an Airflow DAG run is triggered for incremental ingestion.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Wait for Airflow to be ready before streaming so no batches are lost.
    _wait_for_airflow()

    with open(INPUT_FILE, "r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)

        batch_idx = 0
        batch_rows: list[list[str]] = []

        for row in reader:
            batch_rows.append(row)

            if len(batch_rows) >= CHUNK_SIZE:
                batch_file = f"batch_{batch_idx:04d}.csv"
                _write_batch(header, batch_rows, batch_idx)
                _trigger_airflow(batch_file, batch_idx)
                batch_idx += 1
                batch_rows = []
                time.sleep(DELAY_SEC)

        # Write the final partial batch if any rows remain.
        if batch_rows:
            batch_file = f"batch_{batch_idx:04d}.csv"
            _write_batch(header, batch_rows, batch_idx)
            _trigger_airflow(batch_file, batch_idx)
            batch_idx += 1

    print(
        f"Streaming complete. Wrote {batch_idx} batch files to {OUTPUT_DIR}.",
        flush=True,
    )


def _write_batch(
    header: list[str], rows: list[list[str]], batch_idx: int
) -> None:
    """Write a single batch CSV file.

    Parameters
    ----------
    header : list[str]
        Column names from the original CSV.
    rows : list[list[str]]
        Data rows for this batch.
    batch_idx : int
        Zero-based batch sequence number, used for the filename.
    """
    out_path = os.path.join(OUTPUT_DIR, f"batch_{batch_idx:04d}.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    print(
        f"[batch {batch_idx:04d}] Wrote {len(rows)} rows -> {out_path}",
        flush=True,
    )


if __name__ == "__main__":
    stream_csv()
