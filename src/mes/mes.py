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
    
    Query = '''
    SELECT Warehouse.id, Warehouse.piece_id, Pieces.current_piece_type
    FROM Warehouse
    JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
    WHERE Warehouse.warehouse = 1 AND Pieces.current_piece_type = 1 AND Warehouse.piece_status = 'Allocated'
    ORDER BY Warehouse.id ASC;
    ''' 

    cur.execute(Query)
    pieces = cur.fetchall()
    
    # pieces = [][warehouse_id, warehouse, piece_id, piece_type, piece_status]
    # pieces = [][warehouse_id, piece_id, piece_type]
    
    
    if pieces == []:
        print("No pieces to pop")
        return -1
    
    for piece in pieces:
        
        ValueCheck(L_x_ready, True) # Wait for the line to be ready
        
        cur.execute("INSERT INTO TrafficPieces (piece_id, line_id) VALUES (%s, %s);",(piece[1], line,))
        cur.execute("DELETE FROM Warehouse WHERE id = %s;", (piece[0],))
        
        piece_struct = []
        # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        # Transformation_times_array = [time1, time2]
        # Transformation_tools_array = [tool1, tool2]
        # Transformation_types_array = [type1, type2, type3]
        #                                in     mid    out
        
        
        # hard coded values for p3 production in line 1 machine 1
        
        piece_struct.append(0)          # Accumulated time
        piece_struct.append(piece[2])   # Current type
        piece_struct.append(0)          # Index
        piece_struct.append(piece[1])   # Piece ID
        piece_struct.append([45000, 0]) # Transformation times
        piece_struct.append([1, 0])     # Transformation tools
        piece_struct.append([piece[2], 3, 3])   # Transformation types
        
        set_outgoing_piece_w1(client, line, piece_struct)

        setValueCheck(spawnIn_L_x, True, ua.VariantType.Boolean)
        ValueCheck(L_x_ready, False)
        setValueCheck(spawnIn_L_x, False, ua.VariantType.Boolean)
        
def pop_piece_from_w(conn, client, line, piece_struct):
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

def pop_piece_from_w2(conn, client):
    cur = conn.cursor()
    
    Query = '''
    SELECT piece_id 
    FROM Warehouse 
    WHERE Warehouse.Warehouse = 2
    AND Warehouse.piece_id NOT IN 
    (SELECT piece_id FROM ShippingQueue);
    '''
    
    while True:
    
        cur.execute(Query)
        pieces = cur.fetchall()
        
        if pieces == []:
            time.sleep(0.5)
            print("No pieces to pop")
            continue
            
        for piece in pieces:
            
            piece_id = piece[0]
            
            cur.execute("SELECT current_piece_type FROM Pieces WHERE piece_id = %s;", (piece[0],))
            piece_type = cur.fetchone()[0]
            
            # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
            piece_struct = [0, piece_type, 0, piece_id, [0, 0], [0, 0], [piece_type, 0, 0]]
            
            pop_piece_from_w(conn, client, 0, piece_struct)
            
        
        print(pieces)

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
                
                incoming_piece_struct = get_incoming_piece_from_line(client, i+1)
                # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
                acc_time = (incoming_piece_struct[0] // 1000)   # Convert from ms to s
                curr_type = incoming_piece_struct[1]
                piece_id = incoming_piece_struct[3]
                
                cur.execute("DELETE FROM TrafficPieces WHERE piece_id = %s;", (piece_id,))
                cur.execute("UPDATE Pieces SET accumulated_time = %s, current_piece_type = %s WHERE piece_id = %s;", (acc_time, curr_type, piece_id))
                cur.execute("INSERT INTO Warehouse (warehouse, piece_id, piece_status) VALUES (2, %s, 'Allocated');", (piece_id,)) 
                cur.execute("DELETE FROM OpsTable WHERE piece_id = %s", (piece_id,))

                #Verify: curr_type = fin_type
                cur.execute("SELECT final_piece_type FROM Pieces WHERE piece_id = %s", (piece_id,))
                fin_type = cur.fetchone()[0]

                if(curr_type == fin_type):
                    #Piece doesn't need more work
                    cur.execute("DELETE FROM ToWorkQueue WHERE piece_id = %s", (piece_id,))
                    cur.execute("INSERT INTO ShippingQueue (piece_id) VALUES (%s)", (piece_id,))
                
def new_day(conn):
    #get orders that are ready for production
        #update order status to 'InProduction'
    
    #iterate over all the pieces assinged to the orders
        #add pieces to the work queue
    return

def line_manager(conn, client):
    
    cur = conn.cursor()
    
    while True:
    
        request_id, line_id = fulfill_line_request(conn)
        #line id from 1 to 6
        
        if request_id == -1:
            time.sleep(0.5)
            continue #no requests to fulfill
        
        #with request id get op_id, n_ops searching linerequests
        
        cur.execute("SELECT op_id, n_ops FROM LineRequests WHERE request_id = %s;", (request_id,))
        op_id, n_ops = cur.fetchone()
        
        print("op_id: ", op_id, "n_ops: ", n_ops)
        
        #with op_id get piece_id, op_1 and / or op_2, searching ops table if ops_status = 'Requested'
        cur.execute("SELECT piece_id, op_1, op_2 FROM OpsTable WHERE op_id = %s AND ops_status = 'Requested';", (op_id,))
        piece_id, op_1, op_2 = cur.fetchone()
        
        print("piece_id: ", piece_id, "op_1: ", op_1, "op_2: ", op_2)
       
        # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        # Transformation_times_array = [time1, time2]
        # Transformation_tools_array = [tool1, tool2]
        # Transformation_types_array = [type1, type2, type3]
        #                                in     mid    out

        #with piece_id get piece_struct from pieces table
        cur.execute("SELECT accumulated_time, current_piece_type FROM Pieces WHERE piece_id = %s;", (piece_id,))
        acc_time, curr_type = cur.fetchone()
        
        #with op1 and op2 serach for avaiable transformations and get piece_types, tool type and time for each op
        if n_ops == 1:
            cur.execute("SELECT start_piece_type, end_piece_type, tool, processing_time FROM Available_transforms WHERE id = %s;", (op_1,))
            op1_start_piece_type, op1_end_piece_type, op1_tool, op1_time = cur.fetchone()
            
            #Check piece_type
            if curr_type != op1_start_piece_type:
                raise Exception("piece_type does not match")
            
            query = '''
            SELECT line_id, ma.Active_tool, mb.Active_tool
            FROM Lines
            Join Machines AS ma ON Lines.machine_A = ma.machine_id
            Join Machines AS mb ON Lines.machine_B = mb.machine_id
            WHERE line_id = %s;
            '''
            cur.execute(query, (line_id,))
            line_id, ma_tool, mb_tool = cur.fetchone()
            
            if ma_tool == op1_tool:
                print("fill piece struct and pop on Ma")
                #fill piece struct and pop
                Transformation_times_array = [op1_time*1000, 0]
                Transformation_tools_array = [ma_tool, mb_tool]
                Transformation_types_array = [op1_start_piece_type, op1_end_piece_type, op1_end_piece_type]
            elif mb_tool == op1_tool:
                Transformation_times_array = [0, op1_time*1000]
                Transformation_tools_array = [ma_tool, mb_tool]
                Transformation_types_array = [op1_start_piece_type, op1_start_piece_type, op1_end_piece_type]                
                print("fill piece struct and pop on Mb")
                #fill piece struct and pop 
            else:
                print("no tool available")
                raise Exception("no tool available")
                continue
        elif n_ops == 2:
            cur.execute("SELECT start_piece_type, end_piece_type, tool, processing_time FROM Available_transforms WHERE id = %s;", (op_1,))
            op1_start_piece_type, op1_end_piece_type, op1_tool, op1_time = cur.fetchone()
            
            cur.execute("SELECT start_piece_type, end_piece_type, tool, processing_time FROM Available_transforms WHERE id = %s;", (op_2,))
            op2_start_piece_type, op2_end_piece_type, op2_tool, op2_time = cur.fetchone()
            
            #Check piece_type
            if curr_type != op1_start_piece_type or op1_end_piece_type != op2_start_piece_type:
                raise Exception("piece_type does not match")
            
            query = '''
            SELECT line_id, ma.Active_tool, mb.Active_tool
            FROM Lines
            Join Machines AS ma ON Lines.machine_A = ma.machine_id
            Join Machines AS mb ON Lines.machine_B = mb.machine_id
            WHERE line_id = %s;
            '''
            cur.execute(query, (line_id,))
            line_id, ma_tool, mb_tool = cur.fetchone()
            
            if ma_tool == op1_tool and mb_tool == op2_tool:
                Transformation_times_array = [op1_time*1000, op2_time*1000]
                Transformation_tools_array = [ma_tool, mb_tool]
                Transformation_types_array = [op1_start_piece_type, op1_end_piece_type, op2_end_piece_type]
                print("fill piece struct and pop on Ma and Mb")
                #fill piece struct and pop
            else:
                print("no tool available")
                raise Exception("no tool available")
                continue
        
        piece_struct = [acc_time, curr_type, 0, piece_id, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        
        cur.execute("DELETE FROM LineRequests WHERE request_id = %s;", (request_id,))
        
        pop_piece_from_w(conn, client, line_id, piece_struct)
     

        
def main():
    conn = connect_to_postgresql() # Connect to the database
    
    global EPOCH
    EPOCH = setEpoch(conn)
    
    updateDay()
    
    client = Client(OPCUA_SERVER_ADDRESS) # Connect to the OPCUA server
    global OPCUA_CLIENT
    OPCUA_CLIENT = client
    client.connect()
    
    load_tools(client, conn)
    
    spawn_thread = threading.Thread(target=spawn_manager, args=(conn, client), daemon=True)
    spawn_thread.start()
    
    counter_queue = queue.Queue(maxsize=40)
    
    spawn_counter_producer_thread = threading.Thread(target=spawned_piece_counter_prod, args=(client, counter_queue), daemon=True)
    spawn_counter_producer_thread.start()
    
    spawned_piece_counter_cons_thread = threading.Thread(target=spawned_piece_counter_cons, args=(conn, counter_queue), daemon=True)
    spawned_piece_counter_cons_thread.start()
    
    incoming_w2_thread = threading.Thread(target=incoming_w2, args=(conn, client), daemon=True)
    incoming_w2_thread.start()

    check_TWQ_thread = threading.Thread(target=checks_TWQ, args=(conn,), daemon=True)
    check_TWQ_thread.start()

    check_OpsTable_thread = threading.Thread(target=checks_OpsTable, args=(conn,), daemon=True)
    check_OpsTable_thread.start()

    line_manager_thread = threading.Thread(target=line_manager, args=(conn,client), daemon=True)
    line_manager_thread.start()
    
    incoming_piece_w1_from_w2_thread = threading.Thread(target=incoming_piece_w1_from_w2, args=(conn, client), daemon=True)
    incoming_piece_w1_from_w2_thread.start()
    
    w2_piece_poper_thread = threading.Thread(target=pop_piece_from_w2, args=(conn, client), daemon=True)
    w2_piece_poper_thread.start()
    
    
    
    while True:
        updateDay()
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
        

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