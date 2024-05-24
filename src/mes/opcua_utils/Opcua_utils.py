from opcua import Client,ua


# Set the value of a node and wait until the value is set
def setValueCheck(node, value, variant_type):
    node.set_value(ua.Variant(value, variant_type))
    while node.get_value() != value:
        pass

# Wait until the value of a node is set
def ValueCheck(node, value):
    while node.get_value() != value:
        pass

    
    