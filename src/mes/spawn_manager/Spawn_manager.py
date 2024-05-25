from opcua import ua
from opcua_utils.Opcua_utils import *
import time
import queue


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
                        
                        print(f"C{i+1} is ready to spawn piece {piece[0]}")
                        
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
                        
                        print(f"C{i+1} is ready to spawn piece {piece[0]}")
                        
                        # spawn piece in Cx
                        setValueCheck(spawnInCx_node[i], True, ua.VariantType.Boolean)
                        ValueCheck(CX_ready_node[i], False)
                        setValueCheck(spawnInCx_node[i], False, ua.VariantType.Boolean)
                        cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
                        
                        # pop piece from list in index j
                        pieces.pop(j)
                        break
    
    # print("All pieces spawned")
    
    cur.close()
                         
def spawn_manager(conn, client):
    
    while True:
        
        queue = get_spawn_queue(conn)
        spawn_pieces(conn, client, queue)

def spawned_piece_counter_prod(client, queue):
    
    Cx_upload_n = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.C{i}_upload") for i in range(1, 5)]
    Cx_upload_curr = [node.get_value() for node in Cx_upload_n]
    
    while True:
        
        Cx_upload_prev = [value for value in Cx_upload_curr]
        Cx_upload_curr = [node.get_value() for node in Cx_upload_n]
    
        for i, (Curr, prev) in enumerate(zip(Cx_upload_curr, Cx_upload_prev)):
            if prev and not Curr:    # detect falling edge
                print(f"Piece uploaded from C{i+1}")
                print(f"piece type {1 if i <= 1 else 2} produced")
                queue.put(1 if i <= 1 else 2)
    
def spawned_piece_counter_cons(conn, queue): 
    cur = conn.cursor()
    
    while True:
        if queue.empty():
            time.sleep(0.1)
            continue
        
        piece_type = queue.get()
        
        print(f"Piece of type {piece_type} consumed")
        
        cur.execute("SELECT incoming_id FROM Incoming WHERE piece_status = 'Spawned' AND piece_type = %s ORDER BY incoming_id ASC LIMIT 1;", (piece_type,))
        incoming = cur.fetchone()
        if incoming is None:
            print("WTF IS GOING ON")
            continue
        id = incoming[0]
        cur.execute("UPDATE Incoming SET piece_status = 'InWarehouse' WHERE incoming_id = %s;", (id,))