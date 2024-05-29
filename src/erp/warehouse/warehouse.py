import random

def get_free_warehouse_pieces(conn, piece_type):
    cur = conn.cursor()
    
    Query = '''
    SELECT COUNT(*)
    FROM Warehouse
    JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
    WHERE Warehouse = 1 AND Pieces.current_piece_type = %s AND piece_status = 'Free';
    '''	
    cur.execute(Query, (piece_type,))
    result = cur.fetchone()
    cur.close()
    
    return result[0]

def get_free_incoming_pieces(conn, piece_type):
    cur = conn.cursor()
    
    Query = '''
    SELECT COUNT(*)
    FROM Incoming
    WHERE piece_type = %s AND order_id IS NULL;
    '''	
    cur.execute(Query, (piece_type,))
    result = cur.fetchone()
    cur.close()
    
    return result[0]


def alocate_warehouse_piece_to_order(conn, order_id, piece_type):
    cur = conn.cursor()
    Query = '''
    SELECT Warehouse.piece_id
    FROM Warehouse
    JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
    WHERE Warehouse.Warehouse = 1 AND Pieces.current_piece_type = %s AND Warehouse.piece_status = 'Free'
    ORDER BY Warehouse.id ASC
    LIMIT 1;
    '''
    cur.execute(Query, (piece_type,))
    piece_id = cur.fetchone()[0]
    
    cur.execute("SELECT final_piece_type FROM Orders WHERE order_id = %s;", (order_id,))
    final_piece_type = cur.fetchone()[0]
    
    
    cur.execute("UPDATE Warehouse SET piece_status = 'Allocated' WHERE piece_id = %s;", (piece_id,))
    cur.execute("UPDATE Pieces SET order_id = %s, final_piece_type = %s, accumulated_time = 0 WHERE piece_id = %s;", (order_id, final_piece_type, piece_id,))
    print("Avaiable Piece", piece_id, "allocated to order", order_id)
    

def alocate_incoming_piece_to_orders(conn, order_id, piece_type):
    cur = conn.cursor()   
    
    cur.execute("SELECT incoming_id FROM Incoming WHERE piece_type = %s AND order_id IS NULL ORDER BY incoming_id ASC LIMIT 1;", (piece_type,))
    incoming_id = cur.fetchone()[0]
    
    cur.execute("UPDATE Incoming SET order_id = %s WHERE incoming_id = %s;", (order_id, incoming_id,))
    print("Incoming piece", incoming_id, "allocated to order", order_id)
        

def place_buy_order(conn, piece_type, quantity, current_day):
    cur = conn.cursor()
    #select from material costs
    cur.execute("SELECT * FROM MaterialCosts WHERE piece = %s AND supplier = 3;", (piece_type,))    
    selected_vendor = cur.fetchall()
    
    
    if quantity < selected_vendor[0][3]:
        quantity = selected_vendor[0][3]
    
    print("Buying", quantity, "pieces of", piece_type, "from vendor C")
    
    for _ in range(quantity):            
        cur.execute("INSERT INTO Incoming (piece_type, arrival_date, piece_status, cost) VALUES (%s, %s, 'Ordered', %s);", (piece_type, current_day + selected_vendor[0][5], selected_vendor[0][4]))
    #buy from vendor C

def set_pieces_to_spawn(conn, current_day):
    cur = conn.cursor()
    # TODO: set correct query 
    # cur.execute("SELECT incoming_id FROM Incoming WHERE arrival_date <= %s AND piece_status = 'Ordered' ORDER BY incoming_id ASC;", (current_day,))
    # cur.execute("SELECT incoming_id FROM Incoming WHERE piece_status = 'Ordered' ORDER BY incoming_id ASC;")
    # ids = cur.fetchall()
              
    # for id in ids:
    #     print("Requesting piece to spawn")
    #     cur.execute("UPDATE Incoming SET piece_status = 'ToSpawn' WHERE incoming_id = %s;", (id[0], ))
    
    cur.execute("UPDATE Incoming SET piece_status = 'ToSpawn' WHERE arrival_date <= %s AND piece_status = 'Ordered';",(current_day,))
    cur.close()
        

def create_and_place_spawned_pieces_in_warehouse(conn, current_day):
    cur = conn.cursor()
    cur.execute("SELECT piece_type, cost, order_id, incoming_id FROM Incoming WHERE piece_status = 'InWarehouse' ORDER BY incoming_id ASC;")
    
    for incoming_piece in cur.fetchall():
        # [piece_type, cost, order_id, incoming_id]
        
        print( incoming_piece)
        
        
        if incoming_piece[2] == None: # if the piece is not allocated to an order
            piece_status = 'Free'
            cur.execute("INSERT INTO Pieces (current_piece_type, accumulated_cost, arrival_date) VALUES (%s, %s) RETURNING piece_id;", (incoming_piece[0], incoming_piece[1], current_day))
            piece_id = cur.fetchone()[0]
            
        else:   # if the piece is allocated to an order
            piece_status = 'Allocated'
            order_id = incoming_piece[2]
            
            cur.execute("SELECT final_piece_type FROM Orders WHERE order_id = %s;", (order_id,))
            final_piece_type = cur.fetchone()[0]
            
            cur.execute("INSERT INTO Pieces (current_piece_type, accumulated_cost, order_id, final_piece_type, accumulated_time, arrival_date) VALUES (%s, %s, %s, %s, 0, %s) RETURNING piece_id;", (incoming_piece[0], incoming_piece[1], order_id, final_piece_type, current_day))
            piece_id = cur.fetchone()[0]
        
        cur.execute("INSERT INTO Warehouse (warehouse, piece_id, piece_status) VALUES (%s, %s, %s);", (1, piece_id,piece_status,))
        cur.execute("DELETE FROM Incoming WHERE incoming_id = %s;", (incoming_piece[3],))