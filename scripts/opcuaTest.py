from opcua import Client
from opcua import ua
import time

# Function to set the value of a node and check if the value is set
def setValueCheck(node, value, variant_type):
    node.set_value(ua.Variant(value, variant_type))
    while node.get_value() != value:
        pass

# Main code
if __name__ == "__main__":
    # Create a client object
    client = Client("opc.tcp://127.0.0.1:4840")
    
    # Connect to the server
    client.connect()

    # Get the node (UA_test) 
    TestNode = client.get_node("ns=4;s=|var|CODESYS Control Win V3 x64.Application.Manager.UA_test")

    # Set the value of the node to true
    setValueCheck(TestNode, True, ua.VariantType.Boolean)
    print("Value set to True\n")

    # wait for 15 seconds
    time.sleep(15)

    # Set the value of the node to false
    setValueCheck(TestNode, False, ua.VariantType.Boolean)
    print("Value set to False\n")