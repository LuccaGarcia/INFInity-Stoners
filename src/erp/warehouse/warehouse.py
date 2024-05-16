import random

def getFreePieces(conn, piece_type):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Warehouse WHERE piece_type = %s AND piece_status = 'Free';", (piece_type,))
    result = cur.fetchone()
    cur.close()
    
    return result[0]

def alocatePieceToOrder(conn, order_id, piece_type):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Warehouse WHERE piece_type = %s AND piece_status = 'Free' LIMIT 1;", (piece_type,))
    piece = cur.fetchone()

    cur.execute("UPDATE Warehouse SET piece_status = 'Allocated' WHERE piece_id = %s;", (piece[0],))
    conn.commit()
    cur.execute("UPDATE Pieces SET order_id = %s WHERE piece_id = %s;", (order_id, piece[0],))
    conn.commit()
    print("Avaiable Piece", piece[0], "allocated to order", order_id)
    
def alocateIncomingPieceToOrders(conn, order_id, piece_type):
    cur=conn.cursor()
    cur.execute("SELECT * FROM Incoming WHERE piece_type = %s AND order_id IS NULL LIMIT 1;", (piece_type,))
    piece = cur.fetchone()
    cur.execute("UPDATE Incoming SET order_id = %s WHERE incoming_id = %s;", (order_id, piece[0],))
    conn.commit()
    print("Incoming piece", piece[0], "allocated to order", order_id)
    # cur.execute("UPDATE Warehouse SET piece_status = 'Allocated' WHERE piece_id = %s;", (piece[0],))
    

def placeBuyorder(conn, piece_type, quantity, current_day):
    cur = conn.cursor()
    #select from material costs
    cur.execute("SELECT * FROM MaterialCosts WHERE piece = %s AND supplier = 3;", (piece_type,))    
    selected_vendor = cur.fetchall()
    
    
    if quantity < selected_vendor[0][3]:
        quantity = selected_vendor[0][3]
    
    print("Buying", quantity, "pieces of", piece_type, "from vendor C")
    
    for _ in range(quantity):            
        cur.execute("INSERT INTO Incoming (piece_type, arrival_date, piece_status, cost) VALUES (%s, %s, 'Ordered', %s);", (piece_type, current_day + selected_vendor[0][5], selected_vendor[0][4]))
        conn.commit()
    #buy from vendor C

def setPiecesToSpawn(conn, current_day):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Incoming WHERE arrival_date <= %s AND piece_status = 'Ordered';", (current_day,))
    
              
    for piece in cur.fetchall():
        print("Requesting piece to spawn")
        cur.execute("UPDATE Incoming SET piece_status = 'ToSpawn' WHERE incoming_id = %s;", (piece[0], ))
        conn.commit()
        

def createAndPlaceSpawnedPiecesInWarehouse(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Incoming WHERE piece_status = 'Spawned';")
    
    #TODO: mark piece as alocated if order_id is not null
    
    
    
    for incoming_piece in cur.fetchall():
        
        print( incoming_piece)
        piece_status = 'Free' if incoming_piece[5] == None else 'Allocated'
        
        print("New piece spawned, adding to database.")        
        cur.execute("INSERT INTO pieces (current_piece_type, accumulated_cost, order_id) VALUES (%s, %s, %s) RETURNING piece_id;", (incoming_piece[1], incoming_piece[4], incoming_piece[5]))
        #get the id of the inserted piece
        piece_id = cur.fetchone()[0]
        
        print("New piece inserted into warehouse")
        cur.execute("INSERT INTO Warehouse (warehouse, piece_id, piece_type, piece_status) VALUES (%s, %s, %s, %s);", (1, piece_id, incoming_piece[1],piece_status,))
        cur.execute("DELETE FROM Incoming WHERE incoming_id = %s;", (incoming_piece[0],))
        conn.commit()