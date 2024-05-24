from utils.Utils import *
from opcua_utils.Opcua_utils import *
from spawn_manager.Spawn_manager import *
from production_manager.Production_manager import *
from opcua import Client, ua
import time
from dotenv import load_dotenv
import threading
import queue

# Load .env file
load_dotenv()

EPOCH = 0
CURRENT_DAY = 0
CURRENT_SECONDS = 0
DAY_LENGTH = 60
LAST_SECOND = -1
CRONUS = False #if true KILL ALL THE CHILDREN
OPCUA_CLIENT = None

OPCUA_SERVER_ADDRESS = os.getenv("OPCUA_SERVER_ADDRESS")

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

def pop_piece_from_w1_forced(conn, client, line):
    
    spawnIn_L_x = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnIn_L_{line}")
    L_x_ready = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{line}_ready")
    
    
    cur = conn.cursor()

    cur.execute("SELECT * FROM Warehouse WHERE warehouse = 1 AND piece_type = 1 AND piece_status = 'Allocated' ORDER BY id ASC;")
    pieces = cur.fetchall()
    
    # pieces = [][warehouse_id, warehouse, piece_id, piece_type, piece_status]
    
    
    if pieces == []:
        print("No pieces to pop")
        return -1
    
    for piece in pieces:
        
        ValueCheck(L_x_ready, True) # Wait for the line to be ready
        
        cur.execute("INSERT INTO TrafficPieces (piece_id, line_id) VALUES (%s, %s);",(piece[2], line,))
        cur.execute("DELETE FROM Warehouse WHERE id = %s;", (piece[0],))
        
        piece_struct = []
        # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        # Transformation_times_array = [time1, time2]
        # Transformation_tools_array = [tool1, tool2]
        # Transformation_types_array = [type1, type2, type3]
        #                                in     mid    out
        
        
        # hard coded values for p3 production in line 1 machine 1
        piece_struct.append(0)
        piece_struct.append(piece[3])
        piece_struct.append(0)
        piece_struct.append(piece[2])
        piece_struct.append([45000, 0])
        piece_struct.append([1, 0])
        piece_struct.append([piece[3], 3, 3])
        
        set_outgoing_piece_w1(client, line, piece_struct)

        setValueCheck(spawnIn_L_x, True, ua.VariantType.Boolean)
        ValueCheck(L_x_ready, False)
        setValueCheck(spawnIn_L_x, False, ua.VariantType.Boolean)
        
def pop_piece_from_w1(conn, client, line, piece_struct):
    # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
    # Transformation_times_array = [time1, time2]
    # Transformation_tools_array = [tool1, tool2]
    # Transformation_types_array = [type1, type2, type3]
    #                                in     mid    out
    
    cur = conn.cursor()
    
    spawnIn_L_x = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnIn_L_{line}")
    L_x_ready = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{line}_ready")
    
    ValueCheck(L_x_ready, True) # Wait for the line to be ready
    
    piece_id = piece_struct[3]
    
    cur.execute("DELETE FROM Warehouse WHERE id = %s;", (piece_id,)) 

    set_outgoing_piece_w1(client, line, piece_struct) # Set the piece data to be sent to the line
    
    setValueCheck(spawnIn_L_x, True, ua.VariantType.Boolean)
    ValueCheck(L_x_ready, False)
    setValueCheck(spawnIn_L_x, False, ua.VariantType.Boolean)
    
    cur.execute("INSERT INTO TrafficPieces (piece_id, line_id) VALUES (%s, %s);",(piece_id, line,))
    
def incoming_w2(conn, client):
    
    cur = conn.cursor()
    
    
    L_x_upload_W2_n = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{i}_upload_W2") for i in range(1, 7)]
    
    L_x_upload_W2_cur = [value.get_value() for value in L_x_upload_W2_n]
    
    while True:
        
        L_x_upload_W2_prev = [value for value in L_x_upload_W2_cur]
        L_x_upload_W2_cur = [value.get_value() for value in L_x_upload_W2_n]
        
        for i, (curr, prev) in enumerate(zip(L_x_upload_W2_cur, L_x_upload_W2_prev)):
            if prev and not curr: # Detect falling edge
                print(f"Piece uploaded from L{i+1} to W2")
                
                incoming_piece_struct = get_incoming_piece_w2(client, i+1)
                # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
                acc_time = incoming_piece_struct[0]
                curr_type = incoming_piece_struct[1]
                piece_id = incoming_piece_struct[3]
                
                cur.execute("DELETE FROM TrafficPieces WHERE piece_id = %s;", (piece_id,))
                cur.execute("UPDATE Pieces SET accumulated_time = %s, current_piece_type = %s WHERE piece_id = %s;", (acc_time, curr_type, piece_id))
                cur.execute("INSERT INTO Warehouse (warehouse, piece_id, piece_type, piece_status) VALUES (2, %s, %s, 'Allocated');", (piece_id, curr_type))
                
                


    

def main():
    conn = connect_to_postgresql() # Connect to the database
    
    global EPOCH
    EPOCH = setEpoch(conn)
    
    updateDay()
    
    client = Client(OPCUA_SERVER_ADDRESS) # Connect to the OPCUA server
    global OPCUA_CLIENT
    OPCUA_CLIENT = client
    client.connect()
    
    
    spawn_thread = threading.Thread(target=spawn_manager, args=(conn, client), daemon=True)
    spawn_thread.start()
    
    counter_queue = queue.Queue(maxsize=40)
    
    spawn_counter_producer_thread = threading.Thread(target=spawned_piece_counter_prod, args=(client, counter_queue), daemon=True)
    spawn_counter_producer_thread.start()
    
    spawned_piece_counter_cons_thread = threading.Thread(target=spawned_piece_counter_cons, args=(conn, counter_queue), daemon=True)
    spawned_piece_counter_cons_thread.start()
    
    piece_popper_thread = threading.Thread(target=pop_piece_from_w1_forced, args=(conn, client, 1), daemon=True)
    # piece_popper_thread.start()
    
    incoming_w2_thread = threading.Thread(target=incoming_w2, args=(conn, client), daemon=True)
    incoming_w2_thread.start()
    
    
    while True:
        updateDay()
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
        
        pop_piece_from_w1_forced(conn, client, 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        CRONUS = True
        print("Exiting...")
        time.sleep(0.2)
        OPCUA_CLIENT.disconnect()
        print("Disconnected from OPCUA server")
        exit(0)