FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install pandas psycopg2-binary

CMD ["python", "-u", "insert_data.py"]