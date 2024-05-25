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

p5_busy = False    
p6_busy = False
p7_busy = False
p9_busy = False


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
    
    machine_node_ids = ["ns=4;s=|var|CODESYS Control Win V3 x64.Application.C_Manager.C1.MachineTop.CurrentTool", #m1.1#
                        "ns=2;i=1235", 
                        "ns=2;i=1236", 
                        "ns=2;i=1237", 
                        "ns=2;i=1238", 
                        "ns=2;i=1235", 
                        "ns=4;s=|var|CODESYS Control Win V3 x64.Application.C_Manager.C1.MachineBot.CurrentTool", #m2.1#
                        "ns=2;i=1235", 
                        "ns=2;i=1236", 
                        "ns=2;i=1237", 
                        "ns=2;i=1238", 
                        "ns=2;i=1235",] #m2.6 
                        #fill the right values
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
#shitcode starts
def update_piece_type(cur, piece_id, new_type):
    cur.execute("UPDATE pieces SET current_piece_type = %s WHERE piece_id = %s;", (new_type, piece_id))
    cur.connection.commit()

# Belts status (True means occupied, False means free)
# belts_status = [
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt1").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt2").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt3").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt4").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt5").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt6").get_value()
# ]

def handle_p5_1(piece):
                
                belts_status[i] = True # belt is true when activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(1) # incoming type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(3) # mid_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(4) # final_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(45) # time for first transformation
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(15) # time for second transformation
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()
def handle_p5_2(piece):
                
                belts_status[i] = True # belt is true when activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(4) # incoming type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(4) # mid_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(5) # final_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(0) # time for first transformation
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(25) # time for second transformation
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()
def handle_p6(piece):
    
                belts_status[i] = True # belt is true whern activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                for i in range(3):
        if not all(belts_status[:3]):  #idk
            p6_busy = False
            belts_status[i] = True #change i so is the belt number? belt is true when activated
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(1) # incoming type
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(3) # mid_type
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(6) # final_type
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(45) # time for first transformation
            client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(40) # time for second transformation
        else:
            p6_busy = True
            break
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()
def handle_p7(piece):
                
                belts_status[i] = True # belt is true when activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(2) # incoming type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(8) # mid_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(7) # final_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(45) # time for first transformation
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(15) # time for second transformation
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()
def handle_p9_1(piece):
                
                belts_status[i] = True # belt is true when activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(2) # incoming type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(8) # mid_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(8) # final_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(45) # time for first transformation
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(0) # time for second transformation
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()
def handle_p9_2(piece):
                
                belts_status[i] = True # belt is true when activated
                cur = conn.cursor()
                # Execute the query
                cur.execute("SELECT piece_id FROM warehouse WHERE piece_type = %s;", (piece_type))
                # Fetch the result
                piece_id = cur.fetchone()
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[0]").set_value(8) # incoming type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[1]").set_value(9) # mid_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_type_array[2]").set_value(9) # final_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Curr_type").get_value() # current_type
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Piece_id").set_value(piece_id) # we get this value from postgres
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[0]").set_value(45) # time for first transformation
                client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{i}.Transformation_time_array[1]").set_value(0) # time for second transformation
                # we need to extract the acc_time and the current_type
                # Close communication with the server
                cur.close()

def process_orders(pieces):
    # Sort orders based on order ID
    pieces.sort(key=lambda x: int(x['order_id']))

    for piece in pieces:
        if piece['final_piece_type'] == 'P5':
            handle_p5(piece)
        elif piece['final_piece_type'] == 'P6':
            handle_p6(piece)
        elif piece['final_piece_type'] == 'P7':
            handle_p7(piece)
        elif piece['final_piece_type'] == 'P9':
            handle_p9(piece)
        else:
            pass  # Handle unknown piece type
    cur.close()

#shitcode ends

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
            piece = spawn_queue.get(block=False)
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
    cur.execute("SELECT * FROM Incoming WHERE piece_status = 'ToSpawn' ORDER BY incoming_id ASC;")
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

import psycopg2


    
        # Create a new cursor
       

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
