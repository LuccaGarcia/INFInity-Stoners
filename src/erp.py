import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os
import time
import sys
from utils.Utils import connect_to_postgresql

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

if __name__ == '__main__':
    xml_file = r'orders.xml'
    # orders = parse_xml(xml_file)
    conn = connect_to_postgresql()

    
    
