import xml.etree.ElementTree as ET
import psycopg2
from dotenv import load_dotenv
import os
import time
import sys
from utils.Utils import *
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
LAST_SECOND = -1
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
    
    
def updateDay():
    global CURRENT_DAY
    global CURRENT_SECONDS
    global DAY_LENGTH
    global LAST_SECOND
    
    while LAST_SECOND == CURRENT_SECONDS:
        time.sleep(0.1) # Sleep for a short time to avoid busy waiting
        now = -(-time.time() // 1) #inderger division black magic to round up
        CURRENT_DAY = int((now - EPOCH) // DAY_LENGTH) + 1
        CURRENT_SECONDS = int((now - EPOCH) % DAY_LENGTH)
    
    LAST_SECOND = CURRENT_SECONDS
    
def checkAndPlaceBuyOrder(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE delivery_status = 'Incoming' ORDER BY order_id ASC;")
    orders = cur.fetchall()
    
    order_list = [] # [][(order_id, quantity_p1, quantity_p2)]
    for order in orders:
        order_id = order[0]
        quantity_p1 = order[4] if order[3] <= 7 else 0
        quantity_p2 = order[4] if order[3] > 7 else 0
        order_list.append([order_id, quantity_p1, quantity_p2])
        
        #update the order status	
        cur.execute("UPDATE orders SET delivery_status = 'To order' WHERE order_id = %s;", (order[0],))
        conn.commit()  
    
    AvailableP1 = getFreePieces(conn, 1)
    AvailableP2 = getFreePieces(conn, 2)
    
    #alocate avaialble pieces to orders
    for order in order_list:
        while AvailableP1 > 0 and order[1] > 0:
            alocatePieceToOrder(conn, order[0], 1)
            order[1] -= 1
            AvailableP1 -= 1
        
        while AvailableP2 > 0 and order[2] > 0:
            alocatePieceToOrder(conn, order[0], 2)
            order[2] -= 1
            AvailableP2 -= 1
            
    #calculate the required pieces
    RequiredP1 = sum([order[1] for order in order_list])
    RequiredP2 = sum([order[2] for order in order_list])
    
    #buy the required pieces
    if RequiredP1 > 0:
        placeBuyorder(conn, 1, RequiredP1, CURRENT_DAY)
    if RequiredP2 > 0:
        placeBuyorder(conn, 2, RequiredP2, CURRENT_DAY)
    
    for order in order_list:
        
        while order[1] > 0:
            alocateIncomingPieceToOrders(conn, order[0], 1)
            order[1]  = order[1] - 1
        
        while order[2] > 0:
            alocateIncomingPieceToOrders(conn, order[0], 2)
            order[2] = order[2] - 1
    
    cur.close()

def main():
    conn = connect_to_postgresql()
    
    global EPOCH
    EPOCH = setEpoch(conn)
    
    updateDay()
    
    # Create a queue to store received XML data
    xml_queue = queue.Queue()
    # Create a thread to listen for UDP messages
    udp_thread = threading.Thread(target=udp_listener_and_parser, args=(HOST, PORT, xml_queue), daemon=True)
    udp_thread.start()
    
    # Main program loop
    while True:
        
        # # Update the day and seconds
        # if last_second == CURRENT_SECONDS:
        #     time.sleep(0.1) # Sleep for a short time to avoid busy waiting
        #     updateDay()
        #     continue
        # last_second = CURRENT_SECONDS
        
        updateDay() #function will hang until the next second
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
        
        
        udp_updater(conn, xml_queue) # Process received XML data
        
        checkAndPlaceBuyOrder(conn) # Check if buy orders need to be placed
        
        setPiecesToSpawn(conn, CURRENT_DAY) # Set pieces to spawn if they have arrived

        createAndPlaceSpawnedPiecesInWarehouse(conn) # Create and place spawned pieces in the warehouse
        
        
        
        
        


if __name__ == '__main__':
    main()

    
    
