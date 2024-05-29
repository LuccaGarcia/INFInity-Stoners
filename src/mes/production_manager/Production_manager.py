import time
import networkx as nx

import psycopg2
import os
from dotenv import load_dotenv
def connect_to_postgresql():
    load_dotenv()
    try:
        # Construct the connection string
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        host = os.getenv('DATABASE_HOST')
        
        conn = psycopg2.connect(database=database, user=user, password=password, host=host)
        conn.set_session(autocommit=True)
        print("Connection to PostgreSQL database successful.")
        return conn
    except psycopg2.Error as e:
        print("Error: Unable to connect to the PostgreSQL database:", e)
        return None


def fulfill_line_request(conn, client):
    cur = conn.cursor()
    
    get_ocuppation_query = '''
    SELECT SUM(CASE WHEN line_id = 1 then 1 else 0 end) as line_1,
            SUM(CASE WHEN line_id = 2 then 1 else 0 end) as line_2,
            SUM(CASE WHEN line_id = 3 then 1 else 0 end) as line_3,
            SUM(CASE WHEN line_id = 4 then 1 else 0 end) as line_4,
            SUM(CASE WHEN line_id = 5 then 1 else 0 end) as line_5,
            SUM(CASE WHEN line_id = 6 then 1 else 0 end) as line_6
    FROM TrafficPieces;
    '''

    cur.execute("SELECT request_id, piece_id, lines, n_ops FROM LineRequests ORDER BY piece_id ASC")
    requests = cur.fetchall()
    
    if requests == None:
        return -1, -1 #no requests to fulfill
    
    for request in requests:
        # print("first line request: ", request)

        request_id = request[0]
        piece_id = request[1]
        possible_lines = [int(line) for line in request[2]] #unpack lines_str
        n_ops = request[3]
        
        cur.execute(get_ocuppation_query) #get line ocupation
        ocupation_a = cur.fetchone()
        #[line_1, line_2, line_3, line_4, line_5, line_6]
        
        ocupation = []
        
        #if ocupaion is None, set all to 0
        for i in range(6):
            if ocupation_a[i] == None:
                ocupation.append(0)
            else:
                ocupation.append(ocupation_a[i])
        
        Y = [i for i in range(6)]
        
        sorted_indexes = [x for _, x in sorted(zip(ocupation, Y))]
    
        # print("possible lines: ", possible_lines)
        # print("ocupation: ", ocupation)
        # print("sorted indexes: ", sorted_indexes)
        
        for line_index in sorted_indexes:
            
            Line_ready_n = client.get_node(f"ns=4;s=|var|CODESYS Control Win V3 x64.Application.OPCUA_COMS.L_{line_index + 1}_ready")
            Line_ready = Line_ready_n.get_value()
            
            if line_index + 1 in possible_lines:
                if ocupation[line_index] > 3 or Line_ready == False:
                    # print("line is full")
                    continue
                else:
                    # print("request_id: ", request_id, " would go to line: ", index + 1)
                    return request_id, line_index + 1
        
    return -1, -1 #no requests to fulfill
        
def find_available_lines(conn, op_1, op_2 = None):
    
    cur = conn.cursor()
    
    Query = '''
    SELECT Lines.line_id, Lines.machine_A, ma.Active_tool as Active_tool_A, Lines.machine_B, mb.Active_tool AS Active_tool_B
    FROM Lines
    JOIN Machines AS ma ON Lines.machine_A = ma.machine_id
    JOIN Machines AS mb ON Lines.machine_B = mb.machine_id;
    '''
    
    cur.execute(Query)
    lines = cur.fetchall()
    # lines =[][line_id, machine_A, Active_tool_A, machine_B, Active_tool_B]
    
    # print(lines)
    # print(lines[0], "deve ser 1")
    
    cur.execute("SELECT tool FROM Available_transforms WHERE id = %s;", (op_1,))
    op_1_tool = cur.fetchone()[0]
    cur.execute("SELECT tool FROM Available_transforms WHERE id = %s;", (op_2,))
    op_2_tool = cur.fetchone()
    if op_2_tool != None:
        op_2_tool = op_2_tool[0]
    
    avaiable_lines = []
    
    n_ops = 2
    
    if op_1 != None and op_2 != None:
        # print("looking for 2 ops")
        
        for line in lines:
            
            if line[2] == op_1_tool and line[4] == op_2_tool:
                line_id = line[0]
                avaiable_lines.append(line_id)
        
        if avaiable_lines == []: return find_available_lines(conn, op_1, None)

    
    if op_1 != None and op_2 == None:    
        n_ops = 1
        for line in lines:
            if line[2] == op_1_tool or line[4] == op_1_tool:
                avaiable_lines.append(line[0]) 
            

    if avaiable_lines == []:
        n_ops = 0
    
    return avaiable_lines, n_ops
    
def fill_LineRequests():
    conn = connect_to_postgresql()
    cur = conn.cursor()
    
    while True:
        time.sleep(0.2)
        #get all pending operations
        
        #TODO: maybe the sorting order of this query is not the best
        cur.execute("SELECT op_id, piece_id, op_1, op_2 FROM OpsTable WHERE ops_status = 'Pending' ORDER BY piece_id")
        pending_ops = cur.fetchall()

        for op in pending_ops:
            #[op_id, piece_id, op_1, op_2]
            
            available_lines, n_ops = find_available_lines(conn, op[2], op[3])
            if available_lines == []:
                print("No available lines fodeu, how, como?, porque, sera que estou em alagoinha?")
                raise Exception("No available lines")

            line_str = ""
            
            for line in available_lines:
                line_str += str(line)
                
            cur.execute("INSERT INTO LineRequests (op_id, piece_id, lines, n_ops) VALUES (%s, %s, %s, %s);", (op[0], op[1], line_str, n_ops))
            cur.execute("UPDATE OpsTable SET ops_status = 'Requested' WHERE op_id = %s;", (op[0],))

def fill_OpsTable():
    conn = connect_to_postgresql()
    cur = conn.cursor()
    
    #get all available transformations
    cur.execute("SELECT id, start_piece_type, end_piece_type FROM Available_transforms;")
    transforms = cur.fetchall()
    
    g = nx.Graph() #create graph for all possible transformations
    
    for transform in transforms:
        g.add_edge(transform[1], transform[2], tid=transform[0])
    
    
    # get all piece_id from pieces in ToWorkQueue that are in W1 and not in OpsTable
    Query = '''
    SELECT ToWorkQueue.piece_id 
    FROM ToWorkQueue 
    JOIN Warehouse ON Warehouse.piece_id = ToWorkQueue.piece_id
    WHERE Warehouse.Warehouse = 1
    AND ToWorkQueue.piece_id NOT IN 
    (SELECT piece_id FROM OpsTable);
    '''
    
    while True:
        
        time.sleep(0.2)
        
        cur.execute(Query)
        TW_ids = cur.fetchall()
        if TW_ids != []:
            print("TW_ids: ", TW_ids)
        #[piece_id]

        if TW_ids == None:
            time.sleep(0.2)
            continue

        for id in TW_ids:
            
            cur.execute("SELECT piece_id, current_piece_type, final_piece_type FROM Pieces WHERE piece_id = %s;", (id[0],))
            piece = cur.fetchone()
            #[piece_id, current_piece_type_ final_piece_type]
            
            #somehow create ops vector
            paths = nx.all_simple_edge_paths(g, piece[1], piece[2])
            
            for path in paths:
                print("piece_id: ", id[0])
                print(path)
                print("tid: ", [g.edges[edge]['tid'] for edge in path])
                tids = [g.edges[edge]['tid'] for edge in path]
            
            nops = len(tids)
            
            if nops == 0:
                print("piece_id: ", id[0])
                print("NO PATHS")
                raise Exception("NO PATHS")
            
            #fill ops table -> STATUS = Pending
            if nops == 1:
                cur.execute("INSERT INTO OpsTable (piece_id, op_1, ops_status) VALUES (%s, %s, 'Pending');", (piece[0], tids[0]))
            else:
                cur.execute("INSERT INTO OpsTable (piece_id, op_1, op_2, ops_status) VALUES (%s, %s, %s, 'Pending');", (piece[0], tids[0], tids[1]))
                

