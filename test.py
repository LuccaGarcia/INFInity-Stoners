import os
import psycopg2
from dotenv import load_dotenv

# Load .env file
load_dotenv()
# Get the connection string from the environment variable
conn = psycopg2.connect(database="postgres", user = "LuccaGarcia", password = "corno", host = "34.175.19.58")
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