import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os
import time

# Load .env file
load_dotenv()

# Function to parse XML file and extract order data
def parse_xml(xml_file):
    orders = []
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    for order in root.findall('Order'):
        client_name_id = order.find('Client').attrib['NameId']
        order_number = order.find('Order').attrib['Number']
        work_piece = order.find('Order').attrib['WorkPiece']
        quantity = int(order.find('Order').attrib['Quantity'])
        due_date = int(order.find('Order').attrib['DueDate'])
        late_penalty = float(order.find('Order').attrib['LatePen'])
        early_penalty = float(order.find('Order').attrib['EarlyPen'])
        
        # Get current time in seconds and calculate adjusted due date
        current_time = int(time.time())
        adjusted_due_date = current_time + (due_date * 60)
        
        orders.append((client_name_id, order_number, work_piece, quantity, due_date, late_penalty, early_penalty, current_time, adjusted_due_date))
    
    return orders


# Function to insert parsed data into PostgreSQL database 
def insert_into_postgresql(orders):
    try:
        # Define connection parameters
        DATABASE_NAME = "postgres"
        DATABASE_USER = "postgres"
        DATABASE_PASSWORD = "postgres"
        DATABASE_HOST = "34.175.19.58"
        
        # Construct the connection string
        connection_string = f"dbname='{DATABASE_NAME}' user='{DATABASE_USER}' password='{DATABASE_PASSWORD}' host='{DATABASE_HOST}'"
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')

        conn = psycopg2.connect(connection_string)
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        print("Connection to PostgreSQL database successful.")
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Create table if not exists
        cur.execute('''--begin-sql
                    CREATE TABLE IF NOT EXISTS Orders(
                    ClientNameId TEXT,
                    OrderNumber TEXT,
                    WorkPiece TEXT,
                    Quantity INTEGER,
                    DueDate INTEGER,
                    LatePenalty REAL,
                    EarlyPenalty REAL,
                    CurrentTime INTEGER,
                    AdjustedDueDate INTEGER)
                    --end-sql''')
        
        # Insert data into the table
        cur.executemany('''INSERT INTO Orders (ClientNameId, OrderNumber, WorkPiece, Quantity, DueDate, LatePenalty, EarlyPenalty, CurrentTime, AdjustedDueDate)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', orders)
        conn.commit()
        
        print("Orders inserted into the PostgreSQL database successfully.")
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
    finally:
        # Close the cursor and connection
        if 'cur' in locals() and cur is not None:
            cur.close()
        if 'conn' in locals() and conn is not None:
            conn.close()
            print("Connection closed.")

if __name__ == '__main__':
    xml_file = r'orders.xml'
    orders = parse_xml(xml_file)
    insert_into_postgresql(orders)
