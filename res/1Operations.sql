CREATE TABLE IF NOT EXISTS
  Operations( 
    operation_id SERIAL PRIMARY KEY,
    machine_type INTEGER NOT NULL,
    tool INTEGER NOT NULL);

INSERT INTO
    Operations (
        machine_type,
        tool)
VALUES
    (1 , 1),
    (1 , 2),
    (1 , 3),
    (2 , 1),
    (2 , 2),
    (2 , 3),
    (3 , 1),
    (3 , 4),
    (3 , 5),
    (4 , 1),
    (4 , 4),
    (4 , 6);