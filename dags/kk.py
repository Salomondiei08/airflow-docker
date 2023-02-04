import pandas as pd
import os

path = os.path.curdir

df = pd.read_csv('sales.csv')

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