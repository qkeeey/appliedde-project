Here is our initial tasks draft:
**Person 1 — Data Ingestion + NiFi (ENTRY POINT OWNER)**

🎯 **Goal:**

Take the CSV and turn it into a **data ingestion pipeline**

---

🔧 **Tasks:**

### 1. Prepare dataset

* Clean obvious issues:

  * missing values
  * invalid prices
* Convert CSV → JSON optional but better for pipeline

---

### 2. Build NiFi Flow

**Flow design:**

```text
GetFile → ConvertRecord → Validate → PutFile / Send downstream
```

OR:

```text
GenerateFlowFile → ExecuteScript → RouteOnAttribute
```

---

### 3. Simulate “streaming”

Because this is static data:

👉 Split file into chunks:

* send batches every few seconds

💡 This mimics:

> “Airbnb real-time ingestion”

---

📦 **Deliverables:**

* NiFi flow exported template
* Clean dataset version
* Data being ingested continuously


This image contains the same content:

**Person 1 — Data Ingestion + NiFi (ENTRY POINT OWNER)**

🎯 **Goal:**

Take the CSV and turn it into a **data ingestion pipeline**

---

🔧 **Tasks:**

### 1. Prepare dataset

* Clean obvious issues:

  * missing values
  * invalid prices
* Convert CSV → JSON optional but better for pipeline

---

### 2. Build NiFi Flow

**Flow design:**

```text
GetFile → ConvertRecord → Validate → PutFile / Send downstream
```

OR:

```text
GenerateFlowFile → ExecuteScript → RouteOnAttribute
```

---

### 3. Simulate “streaming”

Because this is static data:

👉 Split file into chunks:

* send batches every few seconds

💡 This mimics:

> “Airbnb real-time ingestion”

---

📦 **Deliverables:**

* NiFi flow exported template
* Clean dataset version
* Data being ingested continuously


**Person 3 — Airflow (PROCESSING OWNER)**

🎯 **Goal:**

Create the brain of the pipeline

---

🔧 **Tasks:**

### 1. Build DAG

```python
airbnb_etl
→ clean_data
→ transform_data
→ load_postgres
→ index_elasticsearch
```

---

### 2. Transformations (IMPORTANT)

Don’t be basic.

Examples:

* create `price_category` low, medium, high
* compute `avg_price_per_area`
* filter invalid listings

---

### 3. Scheduling

* Run DAG every X minutes
* Show logs + task success

---

📦 **Deliverables:**

* DAG file
* Logs showing execution
* Clean processed dataset


**Person 4 — Elasticsearch + Kibana (ANALYTICS OWNER)**

🎯 **Goal:**

Turn data into insights

---

🔧 **Tasks:**

### 1. Index data

* Create Elasticsearch index
* Define mappings:

  * `price` → numeric
  * `neighbourhood` → keyword

---

### 2. Build dashboards

**MUST HAVE:**

📊 **Dashboard 1:**

* Listings per neighbourhood

🏠 **Dashboard 2:**

* Price distribution

🏡 **Dashboard 3:**

* Room type breakdown

---

**Optional to impress:**

* Map visualization NYC areas

---

📦 **Deliverables:**

* Elasticsearch index
* Kibana dashboard export
* Visual demo-ready UI


based on the nyc dataset we chose this is how we can split the work among us, after each one of us finish their respective tasks (hopefully until wednesday, 6th May), we have 4 days to integrate which we will do as a team. Basically the integration part is about the docker compose part and connecting everything and testing our pipeline and the final pipeline should look smth like CSV Dataset->NiFi (batch ingestion simulation)->Airflow (clean + transform)->PostgreSQL (structured storage)->Elasticsearch (indexing)->Kibana (dashboard)