from utils.Utils import *
from opcua_utils.Opcua_utils import *
from spawn_manager.Spawn_manager import *
from opcua import Client, ua
import time
from dotenv import load_dotenv
import threading
import queue

# Load .env file
load_dotenv()

EPOCH = 0
CURRENT_DAY = 0
CURRENT_SECONDS = 0
DAY_LENGTH = 60
LAST_SECOND = -1
CRONUS = False #if true KILL ALL THE CHILDREN
OPCUA_CLIENT = None

OPCUA_SERVER_ADDRESS = os.getenv("OPCUA_SERVER_ADDRESS")

def updateDay():
    global CURRENT_DAY
    global CURRENT_SECONDS
    global DAY_LENGTH
    global LAST_SECOND
    
    while LAST_SECOND == CURRENT_SECONDS:
        time.sleep(0.1) # Sleep for a short time to avoid busy waiting
        now = -(-time.time() // 1) #inderger division black magic to round up
        CURRENT_DAY = int((now - EPOCH) // DAY_LENGTH) + 1
        CURRENT_SECONDS = int((now - EPOCH) % DAY_LENGTH)
    
    LAST_SECOND = CURRENT_SECONDS


def main():
    conn = connect_to_postgresql() # Connect to the database
    
    global EPOCH
    EPOCH = setEpoch(conn)
    
    updateDay()
    
    client = Client(OPCUA_SERVER_ADDRESS) # Connect to the OPCUA server
    global OPCUA_CLIENT
    OPCUA_CLIENT = client
    client.connect()
    
    
    spawn_thread = threading.Thread(target=spawn_manager, args=(conn, client), daemon=True)
    spawn_thread.start()
    
    counter_queue = queue.Queue(maxsize=40)
    
    spawn_counter_producer_thread = threading.Thread(target=spawned_piece_counter_prod, args=(client, counter_queue), daemon=True)
    spawn_counter_producer_thread.start()
    
    spawned_piece_counter_cons_thread = threading.Thread(target=spawned_piece_counter_cons, args=(conn, counter_queue), daemon=True)
    spawned_piece_counter_cons_thread.start()
    
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