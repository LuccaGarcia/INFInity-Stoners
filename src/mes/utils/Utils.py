import psycopg2
from dotenv import load_dotenv
import os

def connect_to_postgresql():
    try:
        # Construct the connection string
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')
        
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        print("Connection to PostgreSQL database successful.")
        return conn
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
        return None