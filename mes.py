import xml.etree.ElementTree as ET
import sys
import psycopg2


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

connection_string = "postgresql://LuccaGarcia:sAgf5iV4Goet@ep-rough-cell-a2on0f0y-pooler.eu-central-1.aws.neon.tech/michal?sslmode=require"

try:
    # Establish a connection to the database
    conn = psycopg2.connect(connection_string)
    print("Connection to PostgreSQL database successful.")

    # Close the connection
    conn.close()
    print("Connection closed.")
except psycopg2.Error as e:
    print("Error: Unable to connect to the PostgreSQL database:", e)

if __name__ == '__main__':
    xml_file =  r'C:\Users\79996\Documents\GitHub\INFInity-Stoners\orders.xml'
    orders = parse_xml(xml_file)
    insert_into_postgresql(orders)
    print("Orders inserted into the PostgreSQL database successfully.")

