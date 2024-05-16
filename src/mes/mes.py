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

def setup_machines_tools():
    defined_tools = [1][1][1][1][5][5][2][2][2][6][4][4] #Z-like numbering of tools
    
    machine_node_ids = ["ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235", "ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238", "ns=2;i=1235",] #fill the right values
    machines_obey = [client.get_node(node_id) for node_id in machine_node_ids]

    for i, value in enumerate(defined_tools):
        machines_obey[i].set_value(value)
    
    setup_correct = all(machines_obey[i].get_value() == defined_tools[i] for i in range(len(defined_tools)))

    if setup_correct:
        print("THE MACHINES ARE SET AND READY TO OBEY, MASTER")
    else:
        print("THE SETUP OF MACHINES IS INCORRECT. WE WILL NOT OBEY ANYMORE.")

    
    TestNode = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.Manager.UA_test")

#def read_orders to  

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