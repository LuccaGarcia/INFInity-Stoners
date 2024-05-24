import psycopg2
from dotenv import load_dotenv
import os
import time

def connect_to_postgresql():
    try:
        # Construct the connection string
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')
        
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        conn.set_session(autocommit=True)
        print("Connection to PostgreSQL database successful.")
        return conn
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
        return None
    
def setEpoch(conn):
    cur = conn.cursor()
    #read the epoch from the database if it exists
    cur.execute("SELECT epoch FROM Bigbang;")
    result = cur.fetchone()
    
    #if not, set the epoch to the current time
    if result is None:
        cur.execute("INSERT INTO Bigbang (epoch) VALUES (%s);", (time.time(),))
        conn.commit()
        print("Epoch set to current time")
    
    
    cur.execute("SELECT epoch FROM Bigbang;")
    result = cur.fetchone()
    global EPOCH
    EPOCH = result[0]
    cur.close()

    return EPOCH
