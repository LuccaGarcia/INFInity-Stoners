import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os
import time
import sys
from utils.Utils import connect_to_postgresql
from warehouse.warehouse import *
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
CURRENT_SECONDS = 0
DAY_LENGTH = 60

# Load .env file
load_dotenv()

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

def handle_xml(conn,xml_data):
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
            cursor.execute("INSERT INTO orders (client_name, order_number, quantity, final_piece_type, due_date, late_penalty, early_penalty, placement_date, delivery_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (client_name, order_number, quantity, work_piece, due_date, late_penalty, early_penalty, CURRENT_DAY, 'Incoming'))
            conn.commit()
            
            
            print("Data inserted successfully.")
    except (psycopg2.Error, AttributeError) as e:
        print(f"Error inserting data: {e}")
    
def udp_updater(conn, xml_queue):
    try:
        # Get data from the queue (blocks until data is available)
        received_data = xml_queue.get(block=False)
        handle_xml(conn, received_data)  # Process the data
    except queue.Empty:
        # Handle situations where no data is available in the queue (optional)
        pass
    
    
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
    global CURRENT_SECONDS
    CURRENT_DAY = int((time.time() - EPOCH) // DAY_LENGTH) + 1
    CURRENT_SECONDS = int((time.time() - EPOCH) % DAY_LENGTH)
    
def checkAndPlaceBuyOrder(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE delivery_status = 'Incoming';")
    orders = cur.fetchall()
    
    requiredP1 = 0
    requiredP2 = 0
    
    for order in orders:
        #if the order is due
        if order [3] <=7:
            requiredP1 += order[4]
        else:
            requiredP2 += order[4] 
        
        #update the order status	
        cur.execute("UPDATE orders SET delivery_status = 'To order' WHERE order_id = %s;", (order[0],))
        conn.commit()
    
    if requiredP1 > getFreePieces(conn, 1):
        print("Not enough P1 pieces")
        placeBuyorder(conn, 1, requiredP1, CURRENT_DAY)
    if requiredP2 > getFreePieces(conn, 2):
        placeBuyorder(conn, 2, requiredP2, CURRENT_DAY)
        print("Not enough P2 pieces")
    
    cur.close()

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
        udp_updater(conn, xml_queue)
        
        checkAndPlaceBuyOrder(conn)
        
        setPiecesToSpawn(conn, CURRENT_DAY)

        createAndPlaceSpawnedPiecesInWarehouse(conn)
        
        updateDay()
        time.sleep(1)
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
        
    

if __name__ == '__main__':
    main()

    
    
