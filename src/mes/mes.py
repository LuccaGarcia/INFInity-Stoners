from utils.Utils import connect_to_postgresql
from opcua import Client
import time
from opcua import ua
from dotenv import load_dotenv
import threading
import queue
import xml.etree.ElementTree as ET


# Load .env file
load_dotenv()

EPOCH = 0
CURRENT_DAY = 0
CURRENT_SECONDS = 0
DAY_LENGTH = 60
LAST_SECOND = -1
CRONUS = False #if true KILL ALL THE CHILDREN
OPCUA_CLIENT = None


def setEpoch(conn):
    """
    This function retrieves the current epoch from the database.
    """
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
    global DAY_LENGTH
    global LAST_SECOND
    
    while LAST_SECOND == CURRENT_SECONDS:
        time.sleep(0.1) # Sleep for a short time to avoid busy waiting
        now = -(-time.time() // 1) #inderger division black magic to round up
        CURRENT_DAY = int((now - EPOCH) // DAY_LENGTH) + 1
        CURRENT_SECONDS = int((now - EPOCH) % DAY_LENGTH)
    
    LAST_SECOND = CURRENT_SECONDS

def setup_machines_tools(): #setting tools for the machines
    defined_tools = [1][1][1][1][5][5][2][2][2][6][4][4] #Z-like numbering of tools
    
    machine_node_ids = ["ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235", "ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235",] #fill the right values
    machines_obey = [Client.get_node(node_id) for node_id in machine_node_ids]

    for i, value in enumerate(defined_tools):
        machines_obey[i].set_value(value)
    
    setup_correct = all(machines_obey[i].get_value() == defined_tools[i] for i in range(len(defined_tools)))

    if setup_correct:
        print("THE MACHINES ARE SET AND READY TO OBEY, MASTER")
    else:
        print("THE SETUP OF MACHINES IS INCORRECT. WE WILL NOT OBEY ANYMORE")


#TODO def produce_peace():
# read table of warehouse from ERP
# if piece_status is allocated and order status is tobedone
# start algorithms made by Joao, change accumulated cost after each step, update status in the end.


# ORDER ID CODING

# P7_00001
# P9_00001
# P8_00001

# when P5 order comes, has bigger priority in belts 5 and 6 over P9

# data we read form opc-ua aka PLC: 
# PIECE_ID FOR ORDER whole WAY, TRANSFORMATION STATUS OF THE PIECE, ARRAY FOR PATH TRANSFORMATION.

# MES KNOWS THE STATUS OF ALL MACHINES, CHOSING THE TRANSFORMATION PATH TO FOLLOW.
# TRANSFORMATION PATHs for mesh to decide based on occupation of machine:
# tbdefined

# activating machines
# TOOLS: t1 for 4 pieces, t2 for 2 pieces, t3 for 1 piece, t4 for 1 piece, t5 for 1, t6 for 1
# T1  T1  T1  T1  T5  T5
# T2  T2  T2  T6  T4  T4  

# ORDER TO MES FROM ERP VIA D
# PIECE_ID(based on ERP.TO SEE WHERE IT IS), ORDER_NUMBER(FROM CLIENT), ORDER_ID, START_TYPE END_TYPE STATUS(0-TODO, 1-WAREHOUSE, 2-PROCESSING, 3-DONE, 4-DELIVERED), DELIVERY DATE(switches when status is delivered), 


#TODO shipping line.
# ORDER_id, type of pieces, number of pieces in order, order is ready to send(full), capacity of dock left [dock line as a number in arrow], dock status matrix each cell of dock is place in dock 4 columns 5 rows) with piece_ID(from previous table) 


# Function to set the value of a node and check if the value is set
def setValueCheck(node, value, variant_type):
    node.set_value(ua.Variant(value, variant_type))
    while node.get_value() != value:
        pass

def ValueCheck(node, value):
    while node.get_value() != value:
        pass

def spawn_pieces(conn, client, spawn_queue):

    global CRONUS

    while not CRONUS:

        if spawn_queue.empty():
            continue

        try:
            # Get data from the queue (blocks until data is available)
            piece= spawn_queue.get(block=False)
            print("Pieces to spawn:", piece)
        except queue.Empty:
            # Handle situations where no data is available in the queue (optional)
            print("No pieces to spawn")    
            continue

        C1_ready = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C1_ready")
        spawnInC1 = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnInC1")

        C2_ready = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C2_ready")
        spawnInC2 = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnInC2")

        C3_ready = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C3_ready")
        spawnInC3 = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnInC3")

        C4_ready = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C4_ready")
        spawnInC4 = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnInC4")

        cur = conn.cursor()


        if piece[1] == 1:
            if C1_ready.get_value() == True:#check conveyor status==free
                #send command to spawn piece
                print("Piece to spawn id:", piece[0])
                setValueCheck(spawnInC1, True, ua.VariantType.Boolean)
                ValueCheck(C1_ready, False)
                setValueCheck(spawnInC1, False, ua.VariantType.Boolean)
                cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                conn.commit()
            elif C2_ready.get_value() == True:
                print("Piece to spawn id:", piece[0])
                setValueCheck(spawnInC2, True, ua.VariantType.Boolean)
                ValueCheck(C2_ready, False)
                setValueCheck(spawnInC2, False, ua.VariantType.Boolean)
                cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                conn.commit()
        elif piece[1] == 2:
            if C3_ready.get_value() == True:
                print("Piece to spawn id:", piece[0])
                setValueCheck(spawnInC3, True, ua.VariantType.Boolean)
                ValueCheck(C3_ready, False)
                setValueCheck(spawnInC3, False, ua.VariantType.Boolean)
                cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                conn.commit()
            elif C4_ready.get_value() == True:
                print("Piece to spawn id:", piece[0])
                setValueCheck(spawnInC4, True, ua.VariantType.Boolean)
                ValueCheck(C4_ready, False)
                setValueCheck(spawnInC4, False, ua.VariantType.Boolean)
                cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                conn.commit()

        cur.close()

def look_for_pieces_toSpawn(conn, spawn_queue_1, spawn_queue_2):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Incoming WHERE piece_status = 'ToSpawn';")
    pieces = cur.fetchall()
    cur.close()

    for piece in pieces:
        if piece[1] == 1:
            spawn_queue_1.put(piece)
        if piece[1] == 2:
            spawn_queue_2.put(piece)


#def read_orders to    
def main():
    conn = connect_to_postgresql()
    
    setEpoch(conn)
    
    updateDay()

    client = Client("opc.tcp://127.0.0.1:4840") # Connect to the server
    global OPCUA_CLIENT
    OPCUA_CLIENT = client
    client.connect() # Connect to the server
    #setup_machines_tools()

    # Create a queue to store received requests to spawn pieces
    spawn_queue_1 = queue.Queue()
    spawn_queue_2 = queue.Queue()
    # Create a thread to look for pieces to spawn
    spawn_thread_1 = threading.Thread(target=spawn_pieces, args=(conn, client, spawn_queue_1), daemon=True)
    spawn_thread_2 = threading.Thread(target=spawn_pieces, args=(conn, client, spawn_queue_2), daemon=True)
    spawn_thread_1.start()
    spawn_thread_2.start()

    # Main program loop
    while True:
        updateDay() #function will hang until the next second
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
    
        look_for_pieces_toSpawn(conn, spawn_queue_1, spawn_queue_2)

        #spawn_pieces(conn, client, spawn_queue_1)
        #spawn_pieces(conn, client)



if __name__ == "__main__":
    
    try:
        main()
    except KeyboardInterrupt:
        CRONUS = True
        print("Exiting...")
        time.sleep(0.1)
        OPCUA_CLIENT.disconnect()
        print("Disconnected from opcua the server")
        exit(0)
