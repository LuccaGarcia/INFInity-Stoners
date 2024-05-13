import random

def getFreePieces(conn, piece_type):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Warehouse WHERE piece_type = %s AND piece_status = 'Free';", (piece_type,))
    result = cur.fetchone()
    cur.close()
    
    return result[0]

def placeBuyorder(conn, piece_type, quantity, current_day):
    cur = conn.cursor()
    #select from material costs
    cur.execute("SELECT * FROM MaterialCosts WHERE piece = %s AND supplier = 3;", (piece_type,))
    
    selected_vendor = cur.fetchall()
    if quantity < selected_vendor[0][3]:
        quantity = selected_vendor[0][3]
    
    for _ in range(quantity):            
        cur.execute("INSERT INTO Incoming (arrival_date, piece_status, cost) VALUES (%s, 'Ordered', %s);", (current_day + selected_vendor[0][5], selected_vendor[0][4]))
        conn.commit()
    #buy from vendor C