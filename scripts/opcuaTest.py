from opcua import Client
from opcua import ua
import time

# Function to set the value of a node and check if the value is set
def setValueCheck(node, value, variant_type):
    node.set_value(ua.Variant(value, variant_type))
    while node.get_value() != value:
        pass
def ValueCheck(node, value):
    while node.get_value() != value:
        time.sleep(0.1)
        pass

# Main code
if __name__ == "__main__":
    # Create a client object
    client = Client("opc.tcp://127.0.0.1:4840")
    
    # Connect to the server
    client.connect()

    line = 1
    spawn_in_U_x_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.spawnIn_U_{line}")
    U_x_ready_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.U_{line}_ready")
    U_x_piece_type_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_U_{line}.Curr_type")
    
    for i in range(5):
        print("Shipping piece type 9 to unloading dock 1")
        # Set the value of the node to i
        ValueCheck(U_x_ready_n, True)
        print(f"Unloading dock {line} is free")
        
        setValueCheck(U_x_piece_type_n, 9, ua.VariantType.UInt32)
        print(f"Piece type: 9")
        
        setValueCheck(spawn_in_U_x_n, True, ua.VariantType.Boolean)
        print(f"Request to spawn piece in unloading dock {line}")
        
        ValueCheck(U_x_ready_n, False)
        print(f"Request accepted. Unloading dock {line} is working.")
        
        setValueCheck(spawn_in_U_x_n, False, ua.VariantType.Boolean)
        print(f"Sleeping for 1 second...")
        print()
        time.sleep(0.1)