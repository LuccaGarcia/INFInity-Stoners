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
PREVIOUS_DAY = 0
CURRENT_SECONDS = 0
LAST_SECOND = -1
DAY_LENGTH = 60

# Load .env file
load_dotenv()

def update_day():
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
            # conn.commit()
            
            
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

def check_and_place_buy_order(conn):
    cur = conn.cursor()
    
    cur.execute("SELECT order_id, final_piece_type, quantity FROM orders WHERE delivery_status = 'Incoming' ORDER BY order_id ASC;")
    orders = cur.fetchall()
    # [][order_id, final_piece_type, quantity]
    
    
    order_list = [] # [][(order_id, quantity_p1, quantity_p2)]
    for order in orders:
        order_id = order[0]
        quantity_p1 = order[2] if order[1] <= 6 else 0  # if final piece type = 1,2,3,4,5,6 buy piece type 1
        quantity_p2 = order[2] if order[1] >= 7 else 0   # if final piece type = 7,8,9 buy piece type 2
        order_list.append([order_id, quantity_p1, quantity_p2])
        
        #update the order status	
        cur.execute("UPDATE orders SET delivery_status = 'Ordered' WHERE order_id = %s;", (order[0],))
        # conn.commit()  
       
    Available_warehouse_P1 = get_free_warehouse_pieces(conn, 1)
    Available_warehouse_P2 = get_free_warehouse_pieces(conn, 2)
    Available_incoming_P1 = get_free_incoming_pieces(conn, 1)
    Available_incoming_P2 = get_free_incoming_pieces(conn, 2)
    
    #alocate avaialble pieces to orders
    for order in order_list:
        while Available_warehouse_P1 > 0 and order[1] > 0:
            alocate_warehouse_piece_to_order(conn, order[0], 1)
            order[1] -= 1
            Available_warehouse_P1 -= 1
        
        while Available_incoming_P1 > 0 and order[1] > 0:
            alocate_incoming_piece_to_orders(conn, order[0], 1)
            order[1] -= 1
            Available_incoming_P1 -= 1
        
        while Available_warehouse_P2 > 0 and order[2] > 0:
            alocate_warehouse_piece_to_order(conn, order[0], 2)
            order[2] -= 1
            Available_warehouse_P2 -= 1
        
        while Available_incoming_P2 > 0 and order[2] > 0:
            alocate_incoming_piece_to_orders(conn, order[0], 2)
            order[2] -= 1
            Available_incoming_P2 -= 1

    #calculate the required pieces
    RequiredP1 = sum([order[1] for order in order_list])
    RequiredP2 = sum([order[2] for order in order_list])
    
    #buy the required pieces
    if RequiredP1 > 0:
        place_buy_order(conn, 1, RequiredP1, CURRENT_DAY)
    if RequiredP2 > 0:
        place_buy_order(conn, 2, RequiredP2, CURRENT_DAY)
    
    for order in order_list:
        
        while order[1] > 0:
            alocate_incoming_piece_to_orders(conn, order[0], 1)
            order[1]  = order[1] - 1
        
        while order[2] > 0:
            alocate_incoming_piece_to_orders(conn, order[0], 2)
            order[2] = order[2] - 1
    
    cur.close()

def set_orders_to_ready_for_production(conn):
    cur = conn.cursor()
    cur.execute("SELECT order_id, quantity FROM orders WHERE delivery_status = 'Ordered';")
    orders = cur.fetchall()
    
    print(orders)
    
    for order in orders:
        Query = '''
        SELECT count(*)
        FROM Warehouse
        JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
        WHERE Warehouse.Warehouse = 1 AND Pieces.order_id = %s;
        '''
        cur.execute(Query,(order[0],))
        count = cur.fetchone()[0]
        
        print(count, order[1], order[0])
        
        if count == order[1]:
            print("All pieces for order", order[0], "are in the warehouse")
            cur.execute("UPDATE orders SET delivery_status = 'Ready for production' WHERE order_id = %s;", (order[0],))

def new_day(conn):
    
    # set_orders_to_ready_for_production(conn)
    
    return

def update_work_queue(conn):
    cur = conn.cursor()
    
    #get all pieces in warehouse with status 'Allocated' and not in work queue
    
    Query = '''
    SELECT piece_id 
    FROM Warehouse 
    WHERE warehouse = 1 AND 
        piece_status = 'Allocated' AND 
        piece_id NOT IN (SELECT piece_id 
                            FROM ToWorkQueue);
    '''
    cur.execute(Query)
    pieces = cur.fetchall()
    
    if pieces == None:
        return
    
    #insert into work queue all pieces that are in warehouse with status 'Allocated' and not in work queue
    for piece in pieces:
        cur.execute("INSERT INTO ToWorkQueue (piece_id) VALUES (%s);", (piece[0],))
        
def main():
    conn = connect_to_postgresql()
    
    global EPOCH, PREVIOUS_DAY
    EPOCH = setEpoch(conn)
    
    update_day()
    
    # Create a queue to store recieved XML data
    xml_queue = queue.Queue()
    
    # Start a thread to listen for UDP messages and parse them
    udp_thread = threading.Thread(target=udp_listener_and_parser, args=(HOST, PORT, xml_queue), daemon=True)
    udp_thread.start()
    
    # Start the main loop
    while True:
        
        update_day()
        
        if CURRENT_DAY != PREVIOUS_DAY: # Call the new_day function when the day changes
            new_day(conn)
            print("New day")
            PREVIOUS_DAY = CURRENT_DAY
    
        
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
        
        udp_updater(conn, xml_queue)
        
        check_and_place_buy_order(conn)
        
        set_pieces_to_spawn(conn, CURRENT_DAY)
        
        create_and_place_spawned_pieces_in_warehouse(conn)
        
        update_work_queue(conn)
    



if __name__ == '__main__':
    main()