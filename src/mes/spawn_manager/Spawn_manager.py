from opcua import ua
from opcua_utils.Opcua_utils import *
import time
import queue

import psycopg2
import os
from dotenv import load_dotenv
def connect_to_postgresql():
    load_dotenv()
    try:
        # Construct the connection string
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')
        
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        conn.set_session(autocommit=True)
        print("Connection to PostgreSQL database successful.")
        return conn
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
        return None


def get_spawn_queue(conn):
    cur = conn.cursor()
    
    cur.execute("SELECT incoming_id, piece_type FROM Incoming WHERE piece_status = 'ToSpawn' ORDER BY incoming_id ASC;")
    pieces = cur.fetchall()
    cur.close()
    
    if pieces == None:
        return []
    
    return pieces

def spawn_pieces(conn, client, pieces):
    
    if pieces == None:
        return
    
    cur = conn.cursor()
    
    # pieces is a list of lists with the following format:
    # [incoming_id, piece_type]
    
    # Get nodes for piece spawning
    CX_ready_node = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C{i}_ready") for i in range(1, 5)]
    spawnInCx_node = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnInC{i}") for i in range(1, 5)]

    # while no free Cx continue
    # else spawn piece in first free Cx
    
    while len(pieces) > 0:
        
        CX_ready_values = [node.get_value() for node in CX_ready_node]
    
        for i, Cx in enumerate(CX_ready_values): # for every incoming belt
            for j, piece in enumerate(pieces):  # for every piece in the list
                if i <= 1:
                    if Cx == True and piece[1] == 1:
                        
                        # print(f"C{i+1} is ready to spawn piece {piece[0]}")
                        
                        # spawn piece in Cx
                        setValueCheck(spawnInCx_node[i], True, ua.VariantType.Boolean)
                        ValueCheck(CX_ready_node[i], False)
                        setValueCheck(spawnInCx_node[i], False, ua.VariantType.Boolean)
                        cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                        
                        # pop piece from list in index j
                        pieces.pop(j)
                        break
                
                if i > 1:
                    if Cx == True and piece[1] == 2:
                        
                        # print(f"C{i+1} is ready to spawn piece {piece[0]}")
                        
                        # spawn piece in Cx
                        setValueCheck(spawnInCx_node[i], True, ua.VariantType.Boolean)
                        ValueCheck(CX_ready_node[i], False)
                        setValueCheck(spawnInCx_node[i], False, ua.VariantType.Boolean)
                        cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                        
                        # pop piece from list in index j
                        pieces.pop(j)
                        break
        
        time.sleep(0.1)
    
    # print("All pieces spawned")
    
    cur.close()
                         
def spawn_manager():
    conn = connect_to_postgresql()
    
    client = create_client()
    client.connect()
    
    while True:
        
        queue = get_spawn_queue(conn)
        spawn_pieces(conn, client, queue)
        time.sleep(0.1)

def spawned_piece_counter_prod(client, queue):
    
    Cx_upload_n = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C{i}_upload") for i in range(1, 5)]
    Cx_upload_curr = [node.get_value() for node in Cx_upload_n]
    
    while True:
        
        Cx_upload_prev = [value for value in Cx_upload_curr]
        Cx_upload_curr = [node.get_value() for node in Cx_upload_n]
    
        for i, (Curr, prev) in enumerate(zip(Cx_upload_curr, Cx_upload_prev)):
            if prev and not Curr:    # detect falling edge
                # print(f"Piece uploaded from C{i+1}")
                # print(f"piece type {1 if i <= 1 else 2} produced")
                queue.put(1 if i <= 1 else 2)
        
        time.sleep(0.1)
    
def spawned_piece_counter_cons(conn, queue): 
    cur = conn.cursor()
    
    while True:
        if queue.empty():
            time.sleep(0.1)
            continue
        
        piece_type = queue.get()
        
        # print(f"Piece of type {piece_type} consumed")
        
        cur.execute("SELECT incoming_id FROM Incoming WHERE piece_status = 'Spawned' AND piece_type = %s ORDER BY incoming_id ASC LIMIT 1;", (piece_type,))
        incoming = cur.fetchone()
        if incoming is None:
            print("WTF IS GOING ON")
            continue
        id = incoming[0]
        cur.execute("UPDATE Incoming SET piece_status = 'InWarehouse' WHERE incoming_id = %s;", (id,))

def incoming_piece_w1_from_w2():
    conn = connect_to_postgresql()
    client = create_client()
    client.connect()
    cur = conn.cursor()
    
    L0_upload_W1_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_0_upload_W1")
    L0_upload_W1_curr = L0_upload_W1_n.get_value()
    
    
    while True:
            
        L0_upload_W1_prev = L0_upload_W1_curr
        L0_upload_W1_curr = L0_upload_W1_n.get_value()
        
        if L0_upload_W1_prev and not L0_upload_W1_curr:
            
            piece_struct = get_incoming_piece_from_line(client, 0)
            piece_id = piece_struct[2]
            
            print("Detected piece", piece_id, " entering W1 from W2")
            print("piece_struct: ", piece_struct)
            
            cur.execute("DELETE FROM TrafficPieces WHERE piece_id = %s;", (piece_id,))
            cur.execute("INSERT INTO Warehouse (piece_id, Warehouse, piece_status) VALUES (%s, 1, 'Allocated');", (piece_id,))

        time.sleep(0.1)
            
                
                
                    