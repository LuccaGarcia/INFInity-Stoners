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

def get_incoming_piece_from_line(client, line):
    
    if line > 5:
        print("Invalid line number")
        return None
    
    Out_Piece_L_x_acctime    = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Acc_time")
    Out_Piece_L_x_curr_type  = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Curr_type")
    Out_Piece_L_x_Index      = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Index")
    Out_Piece_L_x_Piece_id   = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Piece_ID")
    Out_Piece_L_x_Transformation_times_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Transformation_times_array[{i}]") for i in range(2)]
    Out_Piece_L_x_Transformation_tools_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Transformation_tools_array[{i}]") for i in range(2)]
    Out_Piece_L_x_Transformation_types_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Out_Piece_L_{line}.Transformation_types_array[{i}]") for i in range(3)]
    
    piece_struct = []
    # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
    # Transformation_times_array = [time1, time2]
    # Transformation_tools_array = [tool1, tool2]
    # Transformation_types_array = [type1, type2, type3]
    #                                in     mid    out
    
    
    piece_struct.append(Out_Piece_L_x_acctime.get_value())
    piece_struct.append(Out_Piece_L_x_curr_type.get_value())
    piece_struct.append(Out_Piece_L_x_Index.get_value())
    piece_struct.append(Out_Piece_L_x_Piece_id.get_value())
    piece_struct.append([node.get_value() for node in Out_Piece_L_x_Transformation_times_array])
    piece_struct.append([node.get_value() for node in Out_Piece_L_x_Transformation_tools_array])
    piece_struct.append([node.get_value() for node in Out_Piece_L_x_Transformation_types_array])
    
    return piece_struct
    
def set_outgoing_piece_w1(client, line, piece_struct):
    
    # piece_struct = [Acc_time, Curr_type, Index, Piece_ID, Transformation_times_array, Transformation_tools_array, Transformation_types_array]
    # Transformation_times_array = [time1, time2]
    # Transformation_tools_array = [tool1, tool2]
    # Transformation_types_array = [type1, type2, type3]
    #                                in     mid    out
    
    
    if line > 6:
        print("Invalid line number")
        return None
    
    In_Piece_L_x_acctime    = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Acc_time")
    In_Piece_L_x_curr_type  = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Curr_type")
    In_Piece_L_x_Index      = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Index")
    In_Piece_L_x_Piece_id   = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Piece_ID")
    In_Piece_L_x_Transformation_times_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Transformation_times_array[{i}]") for i in range(2)]
    In_Piece_L_x_Transformation_tools_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Transformation_tools_array[{i}]") for i in range(2)]
    In_Piece_L_x_Transformation_types_array = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.In_Piece_L_{line}.Transformation_types_array[{i}]") for i in range(3)]
    
    setValueCheck(In_Piece_L_x_acctime, piece_struct.pop(0), ua.VariantType.UInt32)
    setValueCheck(In_Piece_L_x_curr_type, piece_struct.pop(0), ua.VariantType.UInt32)
    setValueCheck(In_Piece_L_x_Index, piece_struct.pop(0), ua.VariantType.UInt32)
    setValueCheck(In_Piece_L_x_Piece_id, piece_struct.pop(0), ua.VariantType.UInt32)
    
    for node, value in zip(In_Piece_L_x_Transformation_times_array, piece_struct.pop(0)):
        setValueCheck(node, value, ua.VariantType.UInt32)
    
    for node, value in zip(In_Piece_L_x_Transformation_tools_array, piece_struct.pop(0)):
        setValueCheck(node, value, ua.VariantType.UInt32)
    
    for node, value in zip(In_Piece_L_x_Transformation_types_array, piece_struct.pop(0)):
        setValueCheck(node, value, ua.VariantType.UInt32)
    

def load_tools(client, conn):
    
    cur = conn.cursor()
    
    cur.execute("SELECT machine_id, Active_tool FROM Machines")
    machines = cur.fetchall()
    
    Set_Tool_Mx_n = [client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.Set_Tool_M{i}") for i in range(1, 13)]
    
    #print("len(Set_Tool_Mx_n): ", len(Set_Tool_Mx_n))
    
    
    for machine in machines:
        
        machine_id = machine[0]
        active_tool = machine[1]
        
        print(f"Setting tool {active_tool} to machine {machine_id}")
        
        setValueCheck(Set_Tool_Mx_n[machine_id-1], active_tool, ua.VariantType.Int16)
        
        print(f"Tool {active_tool} set to machine {machine_id}")