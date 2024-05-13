from time import time, sleep

EPOCH = 1713394800 # Wed Apr 17 2024 23:00:00 GMT+0000 
DAY_LENGTH = 60

def define_epoch():
    global EPOCH
    EPOCH = time()

define_epoch()

while True:
    # print(time() - EPOCH)
    
    day = int((time() - EPOCH) // DAY_LENGTH) + 1 
    seconds = int((time() - EPOCH) % DAY_LENGTH)
    
    print(f"Day: {day}, Seconds: {seconds}")
    sleep(1)
