from utils.Utils import connect_to_postgresql
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


def main():
    conn = connect_to_postgresql()
    
    setEpoch(conn)
    
    updateDay()
    
    
    
    conn.close()

if __name__ == "__main__":
    main()