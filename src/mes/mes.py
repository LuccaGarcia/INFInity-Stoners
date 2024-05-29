from utils.Utils import *
from opcua_utils.Opcua_utils import *
from spawn_manager.Spawn_manager import *
from production_manager.Production_manager import *
from opcua import Client, ua
import time
from dotenv import load_dotenv
from threading import Thread
from multiprocessing import Process
import queue

# Load .env file
load_dotenv()

EPOCH = 0
CURRENT_DAY = 0
CURRENT_SECONDS = 0
DAY_LENGTH = 60
LAST_SECOND = -1
CRONUS = False #if true KILL ALL THE CHILDREN


def updateDay():
    global CURRENT_DAY
    global CURRENT_SECONDS
    global DAY_LENGTH
    global LAST_SECOND
    
    while LAST_SECOND == CURRENT_SECONDS:
        time.sleep(0.2) # Sleep for a short time to avoid busy waiting
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
        # print("No pieces to pop")
        return -1
    
    for piece in pieces:
        
        ValueCheck(L_x_ready, True) # Wait for the line to be ready
        
        cur.execute("INSERT INTO TrafficPieces (piece_id, line_id) VALUES (%s, %s);",(piece[1], line,))
        cur.execute("DELETE FROM Warehouse WHERE id = %s;", (piece[0],))
        
        piece_struct = []
        # piece_struct = [Acc_time, Curr_type, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        # Transformation_times_array = [time1, time2]
        # Transformation_tools_array = [tool1, tool2]
        # Transformation_types_array = [type1, type2, type3]
        #                                in     mid    out
        
        
        # hard coded values for p3 production in line 1 machine 1
        
        piece_struct.append(0)          # Accumulated time
        piece_struct.append(piece[2])   # Current type
        piece_struct.append(piece[1])   # Piece ID
        piece_struct.append([45000, 0]) # Transformation times
        piece_struct.append([1, 0])     # Transformation tools
        piece_struct.append([piece[2], 3, 3])   # Transformation types
        
        set_outgoing_piece_w1(client, line, piece_struct)

        setValueCheck(spawnIn_L_x, True, ua.VariantType.Boolean)
        ValueCheck(L_x_ready, False)
        setValueCheck(spawnIn_L_x, False, ua.VariantType.Boolean)
        
def pop_piece_from_w(conn, client, line, piece_struct):
    # print(piece_struct)
    # piece_struct = [Acc_time, Curr_type, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
    # Transformation_times_array = [time1, time2]
    # Transformation_tools_array = [tool1, tool2]
    # Transformation_types_array = [type1, type2, type3]
    #                                in     mid    out
    
    cur = conn.cursor()
    
    spawnIn_L_x = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnIn_L_{line}")
    L_x_ready = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{line}_ready")
    
    ValueCheck(L_x_ready, True) # Wait for the line to be ready
    
    piece_id = piece_struct[2]
    
    cur.execute("DELETE FROM Warehouse WHERE piece_id = %s;", (piece_id,)) 

    set_outgoing_piece_w1(client, line, piece_struct) # Set the piece data to be sent to the line
    
    setValueCheck(spawnIn_L_x, True, ua.VariantType.Boolean)
    ValueCheck(L_x_ready, False)
    setValueCheck(spawnIn_L_x, False, ua.VariantType.Boolean)
    
    cur.execute("INSERT INTO TrafficPieces (piece_id, line_id) VALUES (%s, %s);",(piece_id, line,))

def pop_piece_from_w2(client):
    conn = connect_to_postgresql()
    # client = create_client()
    # client.connect()
    cur = conn.cursor()
    
    Query = '''
    SELECT Warehouse.piece_id 
    FROM Warehouse
    JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id 
    WHERE Warehouse.Warehouse = 2
    AND Pieces.current_piece_type != Pieces.final_piece_type;
    '''
    
    while True:
    
        cur.execute(Query)
        pieces = cur.fetchall()
        
        if pieces == []:
            time.sleep(0.2)
            # print("No pieces to pop")
            continue
            
        for piece in pieces:
            
            piece_id = piece[0]
            
            cur.execute("SELECT current_piece_type FROM Pieces WHERE piece_id = %s;", (piece[0],))
            piece_type = cur.fetchone()[0]
            
            # piece_struct = [Acc_time, Curr_type, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
            piece_struct = [0, piece_type, piece_id, [0, 0], [0, 0], [piece_type, 0, 0]]
            
            
            print("poped piece: ", piece_id, " from W2 to W1")
            print("piece_struct: ", piece_struct)
            pop_piece_from_w(conn, client, 0, piece_struct)
            
        time.sleep(0.2)
        # print(pieces)

def incoming_w2_producer(client, incoming_w2_queue):
    
    L_x_upload_W2_n = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{i}_upload_W2") for i in range(1, 7)]
    
    L_x_upload_W2_cur = [value.get_value() for value in L_x_upload_W2_n]
    
    while True:
        
        L_x_upload_W2_prev = [value for value in L_x_upload_W2_cur]
        L_x_upload_W2_cur = [value.get_value() for value in L_x_upload_W2_n]
        
        for i, (curr, prev) in enumerate(zip(L_x_upload_W2_cur, L_x_upload_W2_prev)):
            if prev and not curr: # Detect falling edge
                print(f"Piece uploaded from L{i+1} to W2")
                
                incoming_piece_struct = get_incoming_piece_from_line(client, i+1)
                
                incoming_w2_queue.put(incoming_piece_struct)
                print("produceds piece struct: ", incoming_piece_struct)
        
        time.sleep(0.2)
                
def incoming_w2_consumer(conn, incoming_w2_queue):
    # piece_struct = [Acc_time, Curr_type, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
    
    cur = conn.cursor()
    
    while True:
        
        if incoming_w2_queue.empty():
            time.sleep(0.2)
            continue
        
        incoming_piece_struct = incoming_w2_queue.get()
        
        print("consumed piece struct: ", incoming_piece_struct)
        
        if incoming_piece_struct[0] == None:
            print("WTF time is none?")
            incoming_piece_struct[0] = 0
        
        acc_time = (incoming_piece_struct[0] // 1000)   # Convert from ms to s
        curr_type = incoming_piece_struct[1]
        piece_id = incoming_piece_struct[2]
        
        cur.execute("DELETE FROM TrafficPieces WHERE piece_id = %s;", (piece_id,))
        cur.execute("UPDATE Pieces SET accumulated_time = %s, current_piece_type = %s WHERE piece_id = %s;", (acc_time, curr_type, piece_id))
        cur.execute("INSERT INTO Warehouse (warehouse, piece_id, piece_status) VALUES (2, %s, 'Allocated');", (piece_id,)) 
        cur.execute("DELETE FROM OpsTable WHERE piece_id = %s", (piece_id,))

        #Verify: curr_type = fin_type
        cur.execute("SELECT current_piece_type, final_piece_type FROM Pieces WHERE piece_id = %s", (piece_id,))
        current_piece_type, final_piece_type = cur.fetchone()

        if(current_piece_type == final_piece_type):
            #Piece doesn't need more work
            print("Piece ",piece_id," doesn't need more work")
            cur.execute("DELETE FROM ToWorkQueue WHERE piece_id = %s", (piece_id,))
            cur.execute("SELECT order_id FROM Pieces WHERE piece_id = %s", (piece_id,))
            order_id = cur.fetchone()
            cur.execute("INSERT INTO ShippingQueue (piece_id, order_id) VALUES (%s, %s)", (piece_id, order_id,))

                    
def line_manager():
    conn = connect_to_postgresql()
    client = create_client()
    client.connect()
    cur = conn.cursor()
    
    while True:
    
        request_id, line_id = fulfill_line_request(conn, client)
        #line id from 1 to 6
        
        if request_id == -1:
            time.sleep(0.2)
            continue #no requests to fulfill
        
        #with request id get op_id, n_ops searching linerequests
        
        cur.execute("SELECT op_id, n_ops FROM LineRequests WHERE request_id = %s;", (request_id,))
        op_id, n_ops = cur.fetchone()
        
        print("op_id: ", op_id, "n_ops: ", n_ops)
        
        #with op_id get piece_id, op_1 and / or op_2, searching ops table if ops_status = 'Requested'
        cur.execute("SELECT piece_id, op_1, op_2 FROM OpsTable WHERE op_id = %s AND ops_status = 'Requested';", (op_id,))
        
        result = cur.fetchone()
        
        if result == None:
            continue
        
        
        piece_id, op_1, op_2 = result
        
        print("piece_id: ", piece_id, "op_1: ", op_1, "op_2: ", op_2)
       
        # piece_struct = [Acc_time, Curr_type, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
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
                Transformation_tools_array = [ma_tool, 0]
                Transformation_types_array = [op1_start_piece_type, op1_end_piece_type, op1_end_piece_type]
            elif mb_tool == op1_tool:
                print("fill piece struct and pop on Mb")
                Transformation_times_array = [0, op1_time*1000]
                Transformation_tools_array = [0, mb_tool]
                Transformation_types_array = [op1_start_piece_type, op1_start_piece_type, op1_end_piece_type]                
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
        
        piece_struct = [acc_time*1000, curr_type, piece_id, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
        
        cur.execute("DELETE FROM LineRequests WHERE request_id = %s;", (request_id,))
        
        pop_piece_from_w(conn, client, line_id, piece_struct)
    

def spawned_piece_counter():
    
    client = create_client()
    client.connect()
    
    conn = connect_to_postgresql()

    counter_queue = queue.Queue()
    
    spawned_piece_counter_prod_thread = Thread(target=spawned_piece_counter_prod, args=(client,conn, counter_queue), daemon=True)
    spawned_piece_counter_prod_thread.start()
    
    spawned_piece_counter_cons_thread = Thread(target=spawned_piece_counter_cons, args=(conn, counter_queue), daemon=True)
    spawned_piece_counter_cons_thread.start()
    
    spawned_piece_counter_cons_thread.join()
    spawned_piece_counter_prod_thread.join()
    client.disconnect()
    

def incoming_w2():
    client = create_client()
    client.connect()
    incoming_w2_queue = queue.Queue()
    
    incoming_w2_producer_thread = Thread(target=incoming_w2_producer, args=(client,incoming_w2_queue), daemon=True)
    incoming_w2_producer_thread.start()
    
    incoming_w2_consumer_thread = Thread(target=incoming_w2_consumer, args=(connect_to_postgresql(), incoming_w2_queue), daemon=True)
    incoming_w2_consumer_thread.start() 
    
    
def pop_piece_for_delivery(line, piece_type):
    
    client = create_client()
    client.connect()


    spawn_in_U_x_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnIn_U_{line}")
    U_x_ready_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.U_{line}_ready")
    U_x_piece_type_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_U_{line}.Curr_type")
    
    ValueCheck(U_x_ready_n, True) # Wait for the line to be ready
    
    setValueCheck(U_x_piece_type_n, piece_type, ua.VariantType.UInt32) # Set the piece type to be sent to the line
    
    setValueCheck(spawn_in_U_x_n, True, ua.VariantType.Boolean) # Spawn the piece
    
    ValueCheck(U_x_ready_n, False) # Wait for the piece to be spawned    

    setValueCheck(spawn_in_U_x_n, False, ua.VariantType.Boolean) # Reset the spawn flag
    
    client.disconnect()
    
def purge_shipping_lines(conn,client, line):
    
    cur = conn.cursor()
    
    U_x_empty = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.U_{line}_empty")
    
    if U_x_empty.get_value() == True:
        return
    
    UnloadingOrderU_x = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.UnloadingOrderU_{line}")
    
    setValueCheck(UnloadingOrderU_x, True, ua.VariantType.Boolean)
    ValueCheck(U_x_empty, True)
    setValueCheck(UnloadingOrderU_x, False, ua.VariantType.Boolean)
    
    cur.execute("DELETE FROM ShippingQueue WHERE shipping_line = %s;", (line,))
    
    return
    
    
    
    
    
    

def shipping_orders(conn, epoch):
    
    client = create_client()
    client.connect()
        
    while True:
        
        time.sleep(1)
    
        now = time.time()
        
        current_day = int((now - epoch) // 60) + 1
        
        current_seconds = int((now - epoch) % 60)
        
        
        if current_seconds > 50:
            
            
            
            purge_line_1_thread = Thread(target=purge_shipping_lines, args=(conn, client, 1), daemon=True)
            purge_line_2_thread = Thread(target=purge_shipping_lines, args=(conn, client,  2), daemon=True)
            purge_line_3_thread = Thread(target=purge_shipping_lines, args=(conn, client, 3), daemon=True)
            purge_line_4_thread = Thread(target=purge_shipping_lines, args=(conn, client, 4), daemon=True)
            
            purge_line_1_thread.start()
            purge_line_2_thread.start()
            purge_line_3_thread.start()
            purge_line_4_thread.start()
            
        
        
        if current_seconds > 38:    
            continue
        
        cur = conn.cursor()
        
        
        
        line_occupancy_query = '''
            SELECT SUM(CASE WHEN shipping_line = 1 then 1 else 0 end) as line_1,
                    SUM(CASE WHEN shipping_line = 2 then 1 else 0 end) as line_2,
                    SUM(CASE WHEN shipping_line = 3 then 1 else 0 end) as line_3,
                    SUM(CASE WHEN shipping_line = 4 then 1 else 0 end) as line_4
            FROM ShippingQueue'''
        

        cur.execute("SELECT order_id, final_piece_type, quantity FROM Orders WHERE delivery_status = 'Ready for delivery' AND due_date <= %s ORDER BY order_id", (current_day,))
        orders = cur.fetchall()
        #order = [order_id, final_piece_type, quantity]
        
        if orders == []: # if there is no order ready to ship
            time.sleep(0.2)
            continue
        
            
        for order in orders:    
            
            print("Shipping order: ", order)
            
            quantity = order[2]
            
            required_lines = -(-quantity//6)
            
            print("quantity: ", quantity, "required_lines: ", required_lines)
            
            cur.execute(line_occupancy_query)
            line_occupancy = cur.fetchone()
            
            if line_occupancy == []: # data base problems
                raise Exception("Where are my lines?? :(")
            
            if line_occupancy.count(0) < required_lines: # if there are not enough lines available 
                time.sleep(0.2)
                continue
            
            selected_lines = [i for i, _ in zip([i+1 for i, line in enumerate(line_occupancy) if line == 0] , range(required_lines))]
            
            print("selected_lines: ", selected_lines)
            
            
            for i in range(quantity):
                i = i+1
                print("Shipping piece: ", i, "of", quantity, "from order: ", order[0])
                
                piece_to_pop_query = '''
                SELECT Warehouse.id, Pieces.piece_id
                FROM Warehouse
                JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
                JOIN Orders ON Pieces.order_id = Orders.order_id
                WHERE Warehouse.Warehouse = 2 AND Orders.order_id = %s
                Order BY Pieces.piece_id ASC LIMIT 1;
                '''
                
                cur.execute(piece_to_pop_query,(order[0],))
                result = cur.fetchone()
                # result = [warehouse_id, piece_id]
                
                if result == None:
                    print("No pieces to pop")
                    continue
                
                print("poped piece: ", result[1], " from W2 to U ", selected_lines[-(-i//6)-1])
                
                cur.execute("DELETE FROM Warehouse WHERE id = %s;", (result[0],))
                
                
                pop_piece_for_delivery( selected_lines[-(-i//6)-1], order[1])
                cur.execute("UPDATE ShippingQueue SET shipping_line = %s WHERE piece_id = %s;", (selected_lines[-(-i//6)-1], result[1],))
            
            cur.execute("UPDATE Orders SET delivery_status = 'Delivered', delivery_date = %s WHERE order_id = %s;", (current_day, order[0],))
            
            query = '''
                UPDATE Orders
                SET final_cost = (SELECT SUM(accumulated_cost + accumulated_time + accumulated_cost * (Orders.delivery_date - arrival_date)*0.01)
                                    FROM Pieces
                                    JOIN Orders ON Pieces.order_id = Orders.order_id
                                    WHERE Pieces.order_id = %s)
                WHERE order_id = %s;
                '''
            
            cur.execute(query, (order[0], order[0]))
            
            cur.execute("SELECT due_date, delivery_date, early_penalty, late_penalty FROM Orders WHERE order_id = %s;", (order[0],))
            due_date, delivery_date, early_penalty, late_penalty = cur.fetchone()
            
            if(delivery_date == due_date):
                penalty = 0
            elif(delivery_date > due_date):
                penalty = (delivery_date - due_date) * late_penalty
            elif(delivery_date < due_date):
                penalty = (due_date - delivery_date) * early_penalty
            
            cur.execute("UPDATE Orders SET final_cost = final_cost + %s WHERE order_id = %s;", (penalty, order[0]))
           

def incoming_and_pop_piece():
    
    client = create_client()
    client.connect()
    
    incoming_piece_w1_from_w2_trhread = Thread(target=incoming_piece_w1_from_w2, args=(client,), daemon=True)
    incoming_piece_w1_from_w2_trhread.start()
    
    w2_piece_poper_thread = Thread(target=pop_piece_from_w2, args=(client,), daemon=True)
    w2_piece_poper_thread.start()
    

def main():
    conn = connect_to_postgresql() # Connect to the database

    
    global EPOCH
    EPOCH = setEpoch(conn)
    
    updateDay()
    
    client = create_client() # Connect to the OPCUA server
    global OPCUA_CLIENT
    
    OPCUA_CLIENT = client
        
    client.connect()
    
    load_tools(client, conn)
    
    spawned_piece_counter_process = Process(target=spawned_piece_counter, daemon=True)
    spawned_piece_counter_process.start()
    
    spawn_manager_process = Process(target=spawn_manager, daemon=True)
    spawn_manager_process.start()
    
    incoming_w2_process = Process(target=incoming_w2, daemon=True)
    incoming_w2_process.start()

    fill_Ops_table_process = Process(target=fill_OpsTable, daemon=True)
    fill_Ops_table_process.start()

    fill_lineRequests_process = Process(target=fill_LineRequests, daemon=True)
    fill_lineRequests_process.start()

    line_manager_process = Process(target=line_manager, daemon=True)
    line_manager_process.start()
    
    incoming_and_pop_piece_process = Process(target=incoming_and_pop_piece, daemon=True)
    incoming_and_pop_piece_process.start()
    

    shipping_thread = Thread(target=shipping_orders, args=(conn, EPOCH), daemon=True)
    shipping_thread.start()
    
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