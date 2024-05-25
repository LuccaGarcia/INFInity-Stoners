from opcua import ua
from opcua_utils.Opcua_utils import *
import time
import queue

def look_for_pieces_to_process(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Warehouse WHERE warehouse = 1 AND piece_status = 'Allocated' ORDER BY id ASC LIMIT 1;")
    piece = cur.fetchone()

    process_piece(conn, piece[2])

def process_piece(conn, piece_id):  #piece_id from Pieces table
    cur = conn.cursor()
    cur.execute("SELECT * FROM Pieces Where piece_id = {piece_id} LIMIT 1")
    piece = cur.fetchone()

    


    



