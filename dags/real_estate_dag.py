from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from datetime import datetime, timedelta
import pandas as pd

# Default arguments for the DAG
default_args = {
    'owner': 'me',
    'start_date': datetime(2022, 1, 1),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create a new DAG
dag = DAG(
    'real_estate_data_pipeline',
    default_args=default_args,
    schedule_interval=timedelta(hours=1),
)

# Define a function to read the CSV file
def read_csv():
    df = pd.read_csv('sales.csv')
    return df

# Define a function that cleans the csv file
def clean_and_transform_data(**kwargs):
    df = kwargs['task_instance'].xcom_pull(task_ids='read_csv')
    # Perform data cleaning and transformation here
    df = df.dropna() # remove rows with missing values
    df = df[df['price'] > 0] # remove rows with 0 price
    df['price'] = df['price'].astype(int) # cast price to int
    df['bedrooms'] = df['bedrooms'].astype(int) # cast bedrooms to int
    df['bathrooms'] = df['bathrooms'].astype(float) # cast bathrooms to float
    df['sqft'] = df['sqft'].astype(int) # cast sqft to int
    df['sale_date'] = pd.to_datetime(df['sale_date']) # cast sale_date to datetime
    df = df.rename(columns={'address': 'property_address', 'zipcode': 'property_zipcode'}) # rename columns
    df = df[['property_address','city','property_zipcode','price','bedrooms','bathrooms','sqft','sale_date']]
    return df

# Create the 'housing_market_db' if it does not exist
def create_db():
    conn = psycopg2.connect(dbname="housing_market_db", user="postgres", password="postgres", host="localhost")
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS housing_market_db")
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



# Define a task to read the CSV file
read_csv = PythonOperator(
    task_id='read_csv',
    python_callable=read_csv,
    dag=dag,
)

# Define a task to perform data cleaning and transformation
clean_and_transform = PythonOperator(
    task_id='clean_and_transform',
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
load_data_to_postgres = PostgresOperator(
    task_id='load_data_to_postgres',
    sql='INSERT INTO housing_market (property_address, city,property_zipcode,price,bedrooms,bathrooms,sqft,sale_date) SELECT property_address, city,property_zipcode,price,bedrooms,bathrooms,sqft,sale_date FROM cleaned_data',
    postgres_conn_id='postgres_default',
    dag=dag
)


# Set up the dependencies between tasks
read_csv >> clean_and_transform >> create_db >> load_data_to_postgres