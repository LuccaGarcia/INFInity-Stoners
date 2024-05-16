from utils.Utils import connect_to_postgresql
from opcua import Client
import time

EPOCH = 0
CURRENT_DAY = 0
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

def updateDay():
    global CURRENT_DAY
    CURRENT_DAY = int((time.time() - EPOCH) // DAY_LENGTH) + 1

def setup_machines_tools():
    defined_tools = [1][1][1][1][5][2][2][2][6][4][4] #Z-like numbering of tools
    node_ids = ["ns=2;i=1234", "ns=2;i=1235", "ns=2;i=1236", "ns=2;i=1237", "ns=2;i=1238"]
    nodes = [client.get_node(node_id) for node_id in node_ids]



def read_orders to    
def main():
    conn = connect_to_postgresql()
    
    setEpoch(conn)
    
    updateDay()
    setup_machines_tools()
    
    
    conn.close()

if __name__ == "__main__":
    main()