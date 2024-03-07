import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os

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
        
        orders.append((client_name_id, order_number, work_piece, quantity, due_date, late_penalty, early_penalty))
    
    return orders

# Function to insert parsed data into PostgreSQL database
def insert_into_postgresql(orders):
    try:
        # Get the connection string from the environment variable
        connection_string = os.getenv('DATABASE_URL')
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(connection_string)
        print("Connection to PostgreSQL database successful.")
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Create table if not exists
        cur.execute('''CREATE TABLE IF NOT EXISTS Orders
                     (ClientNameId TEXT, OrderNumber TEXT, WorkPiece TEXT, Quantity INTEGER,
                     DueDate INTEGER, LatePenalty REAL, EarlyPenalty REAL)''')
        
        # Insert data into the table
        cur.executemany('INSERT INTO Orders VALUES (%s, %s, %s, %s, %s, %s, %s)', orders)
        conn.commit()
        
        print("Orders inserted into the PostgreSQL database successfully.")
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
            print("Connection closed.")

if __name__ == '__main__':
    xml_file = r'orders.xml'
    orders = parse_xml(xml_file)
    insert_into_postgresql(orders)
