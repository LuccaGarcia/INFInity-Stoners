import networkx as nx
import matplotlib.pyplot as plt
import psycopg2
from dotenv import load_dotenv
import os
import time


def connect_to_postgresql():
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


# g = nx.Graph([(1, 2,), (2, 4), (1, 3), (3, 4)])
# g = nx.Graph()
# g.add_edge(1, 2, tid=10)
# g.add_edge(2, 4, tid=20)
# g.add_edge(1, 3, tid=30)
# g.add_edge(3, 4, tid=40)


# for path in sorted(nx.all_simple_edge_paths(g, 1, 4)):
#     print(path)
#     print("tid: ", [g.edges[edge]['tid'] for edge in path])

# nx.draw_shell(g, with_labels=True, font_weight='bold')
# plt.show()


conn = connect_to_postgresql()
cur = conn.cursor()

cur.execute("SELECT id, start_piece_type, end_piece_type FROM Available_transforms;")
transforms = cur.fetchall()

g = nx.Graph()

for transform in transforms:
    g.add_edge(transform[1], transform[2], tid=transform[0])
    
for path in sorted(nx.all_simple_edge_paths(g, 1, 5)):
    print(path)
    print("tid: ", [g.edges[edge]['tid'] for edge in path])

nx.draw_shell(g, with_labels=True, font_weight='bold')
plt.show()