"""init_nifi_flow.py -- Programmatically build and start the NiFi ingestion flow.

Uses the NiFi 2.x REST API to create a data ingestion flow that simulates
real-time streaming of the Airbnb CSV dataset.


    GenerateFlowFile (trigger)
        -> ExecuteStreamCommand (runs stream_csv.py -- splits CSV, writes
           500-row batches with 3-second delays)
        -> UpdateAttribute (marks completion metadata)
        -> LogAttribute (logs result)

The heavy lifting (CSV reading, chunking, timed writes) is performed by
``stream_csv.py`` which is invoked by ExecuteStreamCommand.
"""

import os
import sys
import time
import json
import logging

import urllib3
import requests

# Suppress InsecureRequestWarning for self-signed HTTPS certificates.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NIFI_BASE_URL = os.getenv("NIFI_BASE_URL", "https://nifi:8443")
NIFI_USERNAME = os.getenv("NIFI_USERNAME", "admin")
NIFI_PASSWORD = os.getenv("NIFI_PASSWORD", "admin1234567890")
NIFI_INPUT_DIR = os.getenv("NIFI_INPUT_DIR", "/nifi/input")
NIFI_OUTPUT_DIR = os.getenv("NIFI_OUTPUT_DIR", "/nifi/output")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
RATE_DURATION = os.getenv("RATE_DURATION", "3 sec")

MAX_WAIT_RETRIES = 30
RETRY_INTERVAL_SEC = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ===================================================================
# NiFi REST API Client
# ===================================================================
class NiFiClient:
    """Thin wrapper around the NiFi 2.x REST API (HTTPS, single-user auth)."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def wait_for_nifi(self) -> None:
        """Block until the NiFi API is responsive."""
        for attempt in range(1, MAX_WAIT_RETRIES + 1):
            try:
                resp = self.session.get(
                    f"{self.base_url}/nifi-api/access/config",
                    timeout=10,
                )
                if resp.status_code < 500:
                    logger.info(
                        "NiFi API is responsive (attempt %d, HTTP %d).",
                        attempt, resp.status_code,
                    )
                    return
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout):
                pass
            logger.info(
                "Waiting for NiFi... (attempt %d/%d)",
                attempt, MAX_WAIT_RETRIES,
            )
            time.sleep(RETRY_INTERVAL_SEC)
        raise RuntimeError("NiFi did not become available within the timeout.")

    def authenticate(self) -> None:
        """Obtain a JWT bearer token from NiFi single-user auth."""
        resp = self.session.post(
            f"{self.base_url}/nifi-api/access/token",
            data={"username": self.username, "password": self.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code not in (200, 201):
            logger.error("Auth failed: %d %s", resp.status_code, resp.text[:300])
            resp.raise_for_status()
        self.session.headers.update(
            {"Authorization": f"Bearer {resp.text}"}
        )
        logger.info("Authenticated successfully.")

    def get_root_pg_id(self) -> str:
        """Return the root process-group ID."""
        resp = self.session.get(
            f"{self.base_url}/nifi-api/flow/process-groups/root"
        )
        resp.raise_for_status()
        pg_id = resp.json()["processGroupFlow"]["id"]
        logger.info("Root process-group ID: %s", pg_id)
        return pg_id

    # ------------------------------------------------------------------
    # Component creation
    # ------------------------------------------------------------------
    def create_processor(
        self,
        group_id: str,
        name: str,
        proc_type: str,
        position: dict,
        properties: dict | None = None,
        auto_terminate: list[str] | None = None,
        scheduling_period: str | None = None,
    ) -> dict:
        """Create a processor inside *group_id* and return the full entity.

        Parameters
        ----------
        group_id : str
            Parent process-group UUID.
        name : str
            Human-readable processor name shown on the NiFi canvas.
        proc_type : str
            Fully-qualified Java class of the processor.
        position : dict
            ``{"x": float, "y": float}`` canvas coordinates.
        properties : dict, optional
            Processor-specific configuration key-value pairs.
        auto_terminate : list[str], optional
            Relationship names to auto-terminate (not connected).
        scheduling_period : str, optional
            Scheduling period override (e.g., "0 sec" for run-once).

        Returns
        -------
        dict
            The created processor entity (contains ``id`` and ``revision``).
        """
        config: dict = {}
        if properties:
            config["properties"] = properties
        if auto_terminate:
            config["autoTerminatedRelationships"] = auto_terminate
        if scheduling_period:
            config["schedulingPeriod"] = scheduling_period

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": proc_type,
                "name": name,
                "position": position,
                "config": config,
            },
        }

        resp = self.session.post(
            f"{self.base_url}/nifi-api/process-groups/{group_id}/processors",
            json=payload,
        )
        if resp.status_code >= 400:
            logger.error(
                "Failed to create processor '%s': %d %s",
                name, resp.status_code, resp.text[:500],
            )
        resp.raise_for_status()
        entity = resp.json()
        logger.info("Created processor '%s' (ID: %s)", name, entity["id"])
        return entity

    def create_connection(
        self,
        group_id: str,
        source_id: str,
        dest_id: str,
        relationships: list[str],
    ) -> dict:
        """Create a connection between two processors.

        Parameters
        ----------
        group_id : str
            Parent process-group UUID.
        source_id : str
            Source processor UUID.
        dest_id : str
            Destination processor UUID.
        relationships : list[str]
            Relationship names to route through this connection.

        Returns
        -------
        dict
            The created connection entity.
        """
        payload = {
            "revision": {"version": 0},
            "component": {
                "source": {
                    "id": source_id,
                    "groupId": group_id,
                    "type": "PROCESSOR",
                },
                "destination": {
                    "id": dest_id,
                    "groupId": group_id,
                    "type": "PROCESSOR",
                },
                "selectedRelationships": relationships,
            },
        }
        resp = self.session.post(
            f"{self.base_url}/nifi-api/process-groups/{group_id}/connections",
            json=payload,
        )
        if resp.status_code >= 400:
            logger.error(
                "Failed to create connection: %d %s",
                resp.status_code, resp.text[:500],
            )
        resp.raise_for_status()
        entity = resp.json()
        logger.info(
            "Connected %s -[%s]-> %s",
            source_id[:8],
            ", ".join(relationships),
            dest_id[:8],
        )
        return entity

    def start_process_group(self, group_id: str) -> None:
        """Set all processors in *group_id* to RUNNING."""
        payload = {"id": group_id, "state": "RUNNING"}
        resp = self.session.put(
            f"{self.base_url}/nifi-api/flow/process-groups/{group_id}",
            json=payload,
        )
        resp.raise_for_status()
        logger.info("Started all processors in group %s.", group_id)


# ===================================================================
# Flow construction 
# ===================================================================
def build_flow(client: NiFiClient, group_id: str) -> None:
    """Create the ingestion flow using NiFi 2.x processors.

    Flow::

        GenerateFlowFile (trigger once)
            -> ExecuteStreamCommand (python3 stream_csv.py)
            -> UpdateAttribute (add completion metadata)
            -> [auto-terminate]

    The actual CSV splitting and timed streaming is performed by
    ``stream_csv.py`` which runs inside the NiFi container via
    ExecuteStreamCommand.

    Parameters
    ----------
    client : NiFiClient
        Authenticated NiFi API client.
    group_id : str
        Process-group ID to place processors into.
    """
    # 1. GenerateFlowFile -- trigger the streaming process once.
    #    Set to a very long scheduling period so it fires exactly once
    #    during the container's lifetime (streaming takes ~5 minutes,
    #    next trigger would be at 9999 seconds = ~2.7 hours).
    generate = client.create_processor(
        group_id=group_id,
        name="GenerateFlowFile - Trigger Stream",
        proc_type="org.apache.nifi.processors.standard.GenerateFlowFile",
        position={"x": 100, "y": 100},
        properties={
            "File Size": "0 B",
            "Unique FlowFiles": "false",
        },
        auto_terminate=None,
        scheduling_period="9999 sec",
    )

    # 2. ExecuteStreamCommand -- runs stream_csv.py
    #    The script reads the CSV, splits into chunks, writes with delays.
    execute = client.create_processor(
        group_id=group_id,
        name="ExecuteStreamCommand - Stream CSV",
        proc_type="org.apache.nifi.processors.standard.ExecuteStreamCommand",
        position={"x": 500, "y": 100},
        properties={
            "Command Path": "/usr/bin/python3",
            "Command Arguments": "/opt/nifi/nifi-current/scripts/stream_csv.py",
            "Working Directory": "/opt/nifi/nifi-current",
            "Argument Delimiter": " ",
        },
        auto_terminate=["nonzero status"],
    )

    # 3. UpdateAttribute -- mark completion with metadata
    update_attr = client.create_processor(
        group_id=group_id,
        name="UpdateAttribute - Stream Complete",
        proc_type="org.apache.nifi.processors.attributes.UpdateAttribute",
        position={"x": 900, "y": 100},
        properties={
            "stream.status": "complete",
            "stream.timestamp": "${now():format('yyyy-MM-dd HH:mm:ss')}",
            "stream.chunk_size": str(CHUNK_SIZE),
        },
    )

    # 4. LogAttribute -- log the completion
    log_attr = client.create_processor(
        group_id=group_id,
        name="LogAttribute - Log Completion",
        proc_type="org.apache.nifi.processors.standard.RouteOnAttribute",
        position={"x": 1300, "y": 100},
        properties={},
        auto_terminate=["matched", "unmatched"],
    )

    # ── Connections ──────────────────────────────────────────────────
    # GenerateFlowFile --success--> ExecuteStreamCommand
    client.create_connection(
        group_id, generate["id"], execute["id"], ["success"]
    )
    # ExecuteStreamCommand --output stream--> UpdateAttribute
    client.create_connection(
        group_id, execute["id"], update_attr["id"],
        ["output stream", "original"],
    )
    # UpdateAttribute --success--> LogAttribute
    client.create_connection(
        group_id, update_attr["id"], log_attr["id"], ["success"]
    )

    logger.info("Flow construction complete.")


# ===================================================================
# Entrypoint
# ===================================================================
def main() -> None:
    """Build and start the NiFi ingestion flow."""
    logger.info("NiFi Flow Initializer starting...")
    logger.info("Target: %s", NIFI_BASE_URL)

    client = NiFiClient(NIFI_BASE_URL, NIFI_USERNAME, NIFI_PASSWORD)

    client.wait_for_nifi()
    client.authenticate()

    root_id = client.get_root_pg_id()
    build_flow(client, root_id)

    client.start_process_group(root_id)

    logger.info(
        "Flow is running. Streaming %d-row batches every %s.",
        CHUNK_SIZE,
        RATE_DURATION,
    )
    logger.info("Input:  %s/AB_NYC_2019.csv", NIFI_INPUT_DIR)
    logger.info("Output: %s", NIFI_OUTPUT_DIR)


if __name__ == "__main__":
    main()
