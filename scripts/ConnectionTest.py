import os
import psycopg2
from dotenv import load_dotenv


def new_day(conn):
    
    cur = conn.cursor()
    
    
    #get orders whose pieces are all in the warehouse

    #get all orders
    cur.execute("SELECT order_id, quantity FROM orders WHERE delivery_status = 'Ordered';")
    orders = cur.fetchall()
    
    print(orders)
    
    for order in orders:
        
        
        Query = '''
        SELECT count(*)
        FROM Warehouse
        JOIN Pieces ON Warehouse.piece_id = Pieces.piece_id
        WHERE Warehouse.Warehouse = 1 AND Pieces.order_id = %s;
        '''
        cur.execute(Query,(order[0],))
        count = cur.fetchone()[0]
        
        print(count, order[1], order[0])
        
        if count == order[1]:
            print("All pieces for order", order[0], "are in the warehouse")
            cur.execute("UPDATE orders SET delivery_status = 'Ready for production' WHERE order_id = %s;", (order[0],))




# Load .env file
load_dotenv()
# Get the connection parameters from the environment variable
database = os.getenv('DATABASE_NAME')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = os.getenv('DATABASE_HOST')

print('Connecting to the PostgreSQL database...')
print('Database:', database)
print('User:', user)
print('Host:', host)

conn = psycopg2.connect(database=database, user=user, password=password, host=host)
conn.autocommit = True
# Create a cursor object
cur = conn.cursor()
# Execute SQL commands to retrieve the current time and version from PostgreSQL
cur.execute('SELECT NOW();')
time = cur.fetchone()[0]
cur.execute('SELECT version();')
version = cur.fetchone()[0]
# Close the cursor and connection
cur.close()

new_day(conn)

conn.close()
# Print the results
print('Current time:', time)
print('PostgreSQL version:', version)