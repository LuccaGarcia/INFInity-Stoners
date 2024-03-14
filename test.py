import os
import psycopg2
from dotenv import load_dotenv

# Load .env file
load_dotenv()
# Get the connection parameters from the environment variable
database = os.getenv('DATABASE_NAME')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = os.getenv('DATABASE_HOST')

conn = psycopg2.connect(database=database, user=user, password=password, host=host)
# Create a cursor object
cur = conn.cursor()
# Execute SQL commands to retrieve the current time and version from PostgreSQL
cur.execute('SELECT NOW();')
time = cur.fetchone()[0]
cur.execute('SELECT version();')
version = cur.fetchone()[0]
# Close the cursor and connection
cur.close()
conn.close()
# Print the results
print('Current time:', time)
print('PostgreSQL version:', version)