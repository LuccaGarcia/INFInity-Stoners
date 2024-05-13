import os
import psycopg2
from dotenv import load_dotenv
import glob

def connect_to_postgresql(superuser=False):
    try:
        # Construct the connection string
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')
        
        if superuser:
            database = os.getenv('SUPERUSER_DATABASE_NAME')
            print("Connecting as superuser")
        
        print('Connecting to the PostgreSQL database...')
        print('Database:', database)
        print('User:', user)
        print('Host:', host)   
        
        
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        print("Connection to PostgreSQL database successful.")
        return conn
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
        return None

def create_tables(conn):
    try:
        cursor = conn.cursor()
        # Get a list of all .sql files in the res folder
        sql_files = glob.glob('res/*.sql')

        # Read and execute each .sql file
        for file in sql_files:
            print(f"Executing {file}")
            with open(file, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
                
        cursor.close()
        conn.commit()
        print("Tables created successfully.")
    except psycopg2.Error as e:
        print("Error: Unable to create tables in the PostgreSQL database:", e)
 
 
def main():
    conn = connect_to_postgresql(superuser=True)
    conn.autocommit = True
    cur = conn.cursor()

    # Drop database if it exists
    cur.execute('DROP DATABASE IF EXISTS erp;')
    # Create a new database

    cur.execute('CREATE DATABASE erp;')
    # Close the cursor and connection
    cur.close()
    # Print the results
    print('Database created successfully.')
    conn.close()
    
    conn = connect_to_postgresql()
    create_tables(conn)
    
    conn.close()
 
        
if __name__ == '__main__':
    main()