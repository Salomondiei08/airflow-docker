from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import os
import psycopg2
import json

# Default arguments for the DAG
default_args = {
    'owner': 'me',
    'start_date': datetime(2023, 2, 3),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create a new DAG
dag = DAG(
    'real_estate_data_pipeline',
    default_args=default_args,
    #  schedule_interval=timedelta(hours=1),
)


# Define a function that cleans the csv file
def clean_and_transform_data():
    path = '/opt/airflow/dags/sales.csv'

    df = pd.read_csv(path)

    # Perform data cleaning and transformation here
    df = df.dropna()  # remove rows with missing values
    df = df[df['price'] > 0]  # remove rows with 0 price
    df['price'] = df['price'].astype(int)  # cast price to int
    df['bedrooms'] = df['bedrooms'].astype(int)  # cast bedrooms to int
    df['bathrooms'] = df['bathrooms'].astype(float)  # cast bathrooms to float
    df['sqft'] = df['sqft'].astype(int)  # cast sqft to int
    df['sale_date'] = pd.to_datetime(df['sale_date'])  # cast sale_date to datetime
    df = df.rename(columns={'address': 'property_address', 'zipcode': 'property_zipcode'})  # rename columns
    df = df[['property_address', 'city', 'property_zipcode', 'price', 'bedrooms', 'bathrooms', 'sqft', 'sale_date']]
    return df


# Create the 'housing_market_db' if it does not exist
def create_db():
    conn = psycopg2.connect(dbname="housing_market_db", user="salomon", password="salomon", host="139.144.169.214")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS housing_market_data (
            id SERIAL PRIMARY KEY,
            property_address VARCHAR(255) NOT NULL,
            city VARCHAR(255) NOT NULL,
            property_zipcode INT NOT NULL,
            price INT NOT NULL,
            bedrooms INT NOT NULL,
            bathrooms REAL NOT NULL,
            sqft INT NOT NULL,
            sale_date TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def insert_into_db():
    conn = psycopg2.connect(dbname="housing_market_db", user="salomon", password="salomon", host="139.144.169.214")
    cur = conn.cursor()
    cur.execute("""
INSERT INTO housing_market_data
(property_address, city, property_zipcode, price, bedrooms, bathrooms, sqft, sale_date)

VALUES
('test', 'Berlin', 33, 3987890, 33, 43, 98, '2016-06-22 19:10:25-07')
    """)
    conn.commit()
    cur.close()
    conn.close()


# Define a task to perform data cleaning and transformation
clean_and_transform = PythonOperator(
    task_id='clean_and_transform_data',
    provide_context=True,
    python_callable=clean_and_transform_data,
    dag=dag
)

# Define a task to create the database
create_db = PythonOperator(
    task_id='create_db',
    python_callable=create_db,
    dag=dag
)

# Define a task to load the data into the Postgres database
insert_into_db = PythonOperator(
    task_id='insert_into_db',
    python_callable=insert_into_db,
    dag=dag
)

# Set up the dependencies between tasks
clean_and_transform >> create_db >> insert_into_db
