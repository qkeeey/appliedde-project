from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'airbnb_pipeline',
    default_args=default_args,
    description='Automated Airbnb ETL Pipeline via Airflow',
    schedule_interval=None,  # Externally triggered by NiFi
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # Process one batch at a time 
    is_paused_upon_creation=False, # Important: Unpaused on creation so it runs on compose up
    tags=['airbnb'],
) as dag:

    # Task 1: Check postgres readiness
    check_postgres = BashOperator(
        task_id='check_postgres',
        bash_command="for i in {1..30}; do pg_isready -h postgres -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-airbnb} && exit 0; sleep 2; done; exit 1",
        append_env=True
    )

    # Task 2: Insert data (receives BATCH_FILE from dag_run.conf)
    insert_data = BashOperator(
        task_id='insert_data',
        bash_command='python /opt/airflow/src/insert_data.py',
        env={"BATCH_FILE": "{{ dag_run.conf.get('batch_file', '') if dag_run.conf else '' }}"},
        append_env=True
    )

    # Task 3: Check elasticsearch readiness
    check_elasticsearch = BashOperator(
        task_id='check_elasticsearch',
        bash_command='for i in {1..30}; do curl -fs http://elasticsearch:9200/_cluster/health && exit 0; sleep 2; done; exit 1',
        append_env=True
    )

    # Task 4: Index into Elasticsearch (receives BATCH_FILE from dag_run.conf)
    index_airbnb = BashOperator(
        task_id='index_airbnb',
        bash_command='python /opt/airflow/src/es_indexer/index_airbnb.py',
        env={"BATCH_FILE": "{{ dag_run.conf.get('batch_file', '') if dag_run.conf else '' }}"},
        append_env=True
    )

    check_postgres >> insert_data
    [insert_data, check_elasticsearch] >> index_airbnb
