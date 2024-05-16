from utils.Utils import connect_to_postgresql
from opcua import Client
import time
from opcua import ua
from dotenv import load_dotenv


# Load .env file
load_dotenv()

EPOCH = 0
CURRENT_DAY = 0
CURRENT_SECONDS = 0
DAY_LENGTH = 60


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
    CURRENT_DAY = int((time.time() - EPOCH) // DAY_LENGTH) + 1
    CURRENT_SECONDS = int((time.time() - EPOCH) % DAY_LENGTH)

def setup_machines_tools(): #setting tools for the machines
    defined_tools = [1][1][1][1][5][5][2][2][2][6][4][4] #Z-like numbering of tools
    
    machine_node_ids = ["ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235", "ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235",] #fill the right values
    machines_obey = [client.get_node(node_id) for node_id in machine_node_ids]

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


# ORDER ID CODING

# P7_00001
# P9_00001
# P8_00001

# when P5 order comes, has bigger priority in belts 5 and 6 over P9

# data we read form opc-ua aka PLC: 
# PIECE_ID FOR ORDER whole WAY, TRANSFORMATION STATUS OF THE PIECE, ARRAY FOR PATH TRANSFORMATION.

# MES KNOWS THE STATUS OF ALL MACHINES, CHOSING THE TRANSFORMATION PATH TO FOLLOW.
# TRANSFORMATION PATHs for mesh to decide based on occupation of machine:
# tbdefined

# activating machines
# TOOLS: t1 for 4 pieces, t2 for 2 pieces, t3 for 1 piece, t4 for 1 piece, t5 for 1, t6 for 1
# T1  T1  T1  T1  T5  T5
# T2  T2  T2  T6  T4  T4  

# ORDER TO MES FROM ERP VIA D
# PIECE_ID(based on ERP.TO SEE WHERE IT IS), ORDER_NUMBER(FROM CLIENT), ORDER_ID, START_TYPE END_TYPE STATUS(0-TODO, 1-WAREHOUSE, 2-PROCESSING, 3-DONE, 4-DELIVERED), DELIVERY DATE(switches when status is delivered), 


#TODO shipping line.
# ORDER_id, type of pieces, number of pieces in order, order is ready to send(full), capacity of dock left [dock line as a number in arrow], dock status matrix each cell of dock is place in dock 4 columns 5 rows) with piece_ID(from previous table) 

"""
def spawn_piece(piece_type):
    if piece_type == 1:
        #check for free upload conveyors
        #verify the change in the codesys 
    if piece_type == 2:
        #check for free upload conveyors
        #verify the change in the codesys
"""

def look_for_pieces_toSpawn(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Incoming WHERE piece_status = 'ToSpawn';")
    
    pieces = cur.fetchall()

    for piece in pieces:
        
        print("Spawning piece ", piece[0])
        #spawn_piece(piece[1])#piece[1] = piece_type

        cur.execute("UPDATE Incoming SET piece_status = 'Spawned' WHERE incoming_id = %s;", (piece[0], ))
        conn.commit()

    cur.close()

#def read_orders to    
def main():
    #client = Client("opc.tcp://127.0.0.1:4840") # Connect to the server
    #client.connect() # Get the node (UA_test) 
    conn = connect_to_postgresql()
    
    setEpoch(conn)
    
    updateDay()
    #setup_machines_tools()
   
    # Main program loop
    while True:
    
        look_for_pieces_toSpawn(conn)

        updateDay()
        time.sleep(1)
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)

if __name__ == "__main__":
    main()