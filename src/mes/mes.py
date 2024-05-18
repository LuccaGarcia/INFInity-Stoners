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
LAST_SECOND = -1


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
    global DAY_LENGTH
    global LAST_SECOND
    
    while LAST_SECOND == CURRENT_SECONDS:
        time.sleep(0.1) # Sleep for a short time to avoid busy waiting
        now = -(-time.time() // 1) #inderger division black magic to round up
        CURRENT_DAY = int((now - EPOCH) // DAY_LENGTH) + 1
        CURRENT_SECONDS = int((now - EPOCH) % DAY_LENGTH)
    
    LAST_SECOND = CURRENT_SECONDS

def setup_machines_tools(): #setting tools for the machines
    defined_tools = [1][1][1][1][5][5][2][2][2][6][4][4] #Z-like numbering of tools
    
    machine_node_ids = ["ns=4;s=|var|CODESYS Control Win V3 x64.Application.C_Manager.C1.MachineTop.CurrentTool", #m1.1#
                        "ns=2;i=1235", 
                        "ns=2;i=1236", 
                        "ns=2;i=1237", 
                        "ns=2;i=1238", 
                        "ns=2;i=1235", 
                        "ns=4;s=|var|CODESYS Control Win V3 x64.Application.C_Manager.C1.MachineBot.CurrentTool", #m2.1#
                        "ns=2;i=1235", 
                        "ns=2;i=1236", 
                        "ns=2;i=1237", 
                        "ns=2;i=1238", 
                        "ns=2;i=1235",] #m2.6 
                        #fill the right values
    machines_obey = [Client.get_node(node_id) for node_id in machine_node_ids]

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
#shitcode starts
def update_piece_type(cur, piece_id, new_type):
    cur.execute("UPDATE pieces SET current_piece_type = %s WHERE piece_id = %s;", (new_type, piece_id))
    cur.connection.commit()

# Belts status (True means occupied, False means free)
# belts_status = [
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt1").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt2").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt3").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt4").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt5").get_value(),
#     client.get_node("ns=2;s=|var|YourPLCProject.Belt6").get_value()
# ]

def handle_p5(piece):
    if all(belts_status[:3]) and belts_status[3] and piece['status'] == 2:
        client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(0)  # P1 Waits until one of the first 3 belts or belt 4 is empty
    elif all(belts_status[:3]) and not belts_status[3] and piece['status'] == 2:
        client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(1)  # P1 gives priority to P7
    elif all(belts_status[:3]) and not belts_status[3] and piece['status'] != 2:
        belts_status[3] = True
        client.get_node("ns=2;s=|var|YourPLCProject.Belt4").set_value(True)
        client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(2)  # P1 goes to belt 4, performs tool 1 for 45s, skips tool 6, turns around for 40s, -> P3
        update_piece_type(piece['piece_id'], 'P3')  # Update current_piece_type to P3
    else:
        for i in range(3):
            if not belts_status[i]:
                belts_status[i] = True
                client.get_node(f"ns=2;s=|var|YourPLCProject.Belt{i+1}").set_value(True)
                client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(3)  # P1 goes to belt {i+1}, performs tool 1 for 45s, tool 2 for 15s, turns around for 40s, -> P4
                update_piece_type(piece['piece_id'], 'P4')  # Update current_piece_type to P4
                break

def handle_p6(piece):
    if all(belts_status[:3]):
        client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(4)  # P1 Waits until any of the first 3 belts is empty
    else:
        for i in range(3):
            if not belts_status[i]:
                belts_status[i] = True
                client.get_node(f"ns=2;s=|var|YourPLCProject.Belt{i+1}").set_value(True)
                client.get_node("ns=2;s=|var|YourPLCProject.P1Status").set_value(5)  # P1 goes to belt {i+1}, performs tool 1 for 45s, tool 2 for 15s, turns around for 40s, -> P4
                update_piece_type(piece['piece_id'], 'P4')  # Update current_piece_type to P4
                break

def handle_p7(piece):
    if belts_status[3] and all(belts_status[:3]):
        client.get_node("ns=2;s=|var|YourPLCProject.P8Status").set_value(0)  # P8 Waits
    elif not belts_status[3]:
        belts_status[3] = True
        client.get_node("ns=2;s=|var|YourPLCProject.Belt4").set_value(True)
        client.get_node("ns=2;s=|var|YourPLCProject.P8Status").set_value(1)  # P8 goes to belt 4, performs tool 1 for 45s, tool 6 for 15s, -> P7
        update_piece_type(piece['piece_id'], 'P7')  # Update current_piece_type to P7
    else:
        for i in range(3):
            if not belts_status[i]:
                belts_status[i] = True
                client.get_node(f"ns=2;s=|var|YourPLCProject.Belt{i+1}").set_value(True)
                client.get_node("ns=2;s=|var|YourPLCProject.P8Status").set_value(2)  # P8 goes to belt {i+1}, performs tool 1 for 45s, skips tool 2, turns around for 40s, -> checks belt 4
                update_piece_type(piece['piece_id'], 'P8')  # Update current_piece_type to P8
                break

def handle_p9(piece):
    if all(belts_status[:3]) and belts_status[3] and piece['status'] == 2:
        client.get_node("ns=2;s=|var|YourPLCProject.P2Status").set_value(0)  # P2 Waits until one of the first 3 belts or belt 4 is empty
    elif all(belts_status[:3]) and not belts_status[3] and piece['status'] == 2:
        client.get_node("ns=2;s=|var|YourPLCProject.P2Status").set_value(1)  # P2 gives priority to P7
    elif all(belts_status[:3]) and not belts_status[3] and piece['status'] != 2:
        belts_status[3] = True
        client.get_node("ns=2;s=|var|YourPLCProject.Belt4").set_value(True)
        client.get_node("ns=2;s=|var|YourPLCProject.P2Status").set_value(2)  # P2 goes to belt 4, performs tool 1 for 45s, skips tool 6, turns around for 40s, -> P8
        update_piece_type(piece['piece_id'], 'P8')  # Update current_piece_type to P8
    else:
        for i in range(3):
            if not belts_status[i]:
                belts_status[i] = True
                client.get_node(f"ns=2;s=|var|YourPLCProject.Belt{i+1}").set_value(True)
                client.get_node("ns=2;s=|var|YourPLCProject.P2Status").set_value(3)  # P2 goes to belt {i+1}, performs tool 1 for 45s, skips tool 2 for 15s, turns around for 40s, -> P8
                update_piece_type(piece['piece_id'], 'P8')  # Update current_piece_type to P8
                break

        # Handle P9 on belts 5 or 6
        if all(belts_status[4:6]):
            client.get_node("ns=2;s=|var|YourPLCProject.P8Status").set_value(0)  # P8 Waits
        else:
            for i in range(4, 6):
                if not belts_status[i]:
                    belts_status[i] = True
                    client.get_node(f"ns=2;s=|var|YourPLCProject.Belt{i+1}").set_value(True)
                    client.get_node("ns=2;s=|var|YourPLCProject.P8Status").set_value(1)  # P8 goes to belt {i+1}, performs tool 5 for 45s, skips tool 4, -> P9
                    update_piece_type(piece['piece_id'], 'P9')  # Update current_piece_type to P9
                    break

def process_orders(pieces):
    # Sort orders based on order ID
    pieces.sort(key=lambda x: int(x['order_id']))

    for piece in pieces:
        if piece['final_piece_type'] == 'P5':
            handle_p5(piece)
        elif piece['final_piece_type'] == 'P6':
            handle_p6(piece)
        elif piece['final_piece_type'] == 'P7':
            handle_p7(piece)
        elif piece['final_piece_type'] == 'P9':
            handle_p9(piece)
        else:
            pass  # Handle unknown piece type
    cur.close()

#shitcode ends
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
        updateDay() #function will hang until the next second
        print("Day:", CURRENT_DAY, "Seconds:", CURRENT_SECONDS)
    
        look_for_pieces_toSpawn(conn)
        #process_orders(pieces)



if __name__ == "__main__":
    main()