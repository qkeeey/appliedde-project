FROM postgres:15

COPY ./sql/schema.sql /docker-entrypoint-initdb.d/schema.sql
COPY ./sql/init_airflow.sql /docker-entrypoint-initdb.d/init_airflow.sql