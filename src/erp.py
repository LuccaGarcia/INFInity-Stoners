import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os
import time
import sys
from utils.Utils import connect_to_postgresql
import asyncio
import socket
import threading
import queue
import xml.etree.ElementTree as ET

# Replace with your desired host and port
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5000

EPOCH = 0
CURRENT_DAY = 0
DAY_LENGTH = 60

def udp_listener_and_parser(host, port, queue):
  """
  This function listens for UDP messages on a specified host and port.
  It parses the received data as XML and adds it to the provided queue.
  """
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((host, port))
  print(f"Listening for UDP messages on {host}:{port}")
  while True:
    data, addr = sock.recvfrom(1024)
    try:
      # Parse the received data as XML
      root = ET.fromstring(data)
      queue.put(root)  # Add parsed data to the queue
    except ET.ParseError as e:
      print(f"Error parsing XML: {e}")

def handle_xml(xml_data, conn):
    """
    This function processes XML data and performs database operations.
    """
    try:
        
        # Parse the XML data

        # Extract client information
        client = xml_data.find('Client')
        client_name = client.attrib['NameId']
        print("Client Name:", client_name)

        # Extract order information
        orders = xml_data.findall('Order')
        print("\nOrders:")
        for order in orders:
            order_number = order.attrib['Number']
            work_piece = order.attrib['WorkPiece']
            quantity = order.attrib['Quantity']
            due_date = order.attrib['DueDate']
            late_penalty = order.attrib['LatePen']
            early_penalty = order.attrib['EarlyPen']
        
            print(f"Order Number: {order_number}, Work Piece: {work_piece}, Quantity: {quantity}, Due Date: {due_date}, Late Penalty: {late_penalty}, Early Penalty: {early_penalty}")
            
            #get number on the end of work piece
            work_piece = int(work_piece[-1])

            # Insert data into the database
            cursor = conn.cursor()
            cursor.execute("INSERT INTO orders (client_name, order_number, quantity, final_piece_type, due_date, late_penalty, early_penalty, placement_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (client_name, order_number, quantity, work_piece, due_date, late_penalty, early_penalty, CURRENT_DAY))
            conn.commit()
            print("Data inserted successfully.")
    except (psycopg2.Error, AttributeError) as e:
        print(f"Error inserting data: {e}")

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

def updateDay():
    global CURRENT_DAY
    CURRENT_DAY = int((time.time() - EPOCH) // DAY_LENGTH) + 1

def main():
    conn = connect_to_postgresql()
    
    setEpoch(conn)
    
    updateDay()
    
    # Create a queue to store received XML data
    xml_queue = queue.Queue()
    
    # Create a thread to listen for UDP messages
    udp_thread = threading.Thread(target=udp_listener_and_parser, args=(HOST, PORT, xml_queue))
    udp_thread.start()
    
    # Main program loop
    while True:
        
        updateDay()
        
        try:
            # Get data from the queue (blocks until data is available)
            received_data = xml_queue.get(block=False)
            handle_xml(received_data, conn)  # Process the data
        except queue.Empty:
            # Handle situations where no data is available in the queue (optional)
            pass
    

if __name__ == '__main__':
    main()

    
    