CREATE TABLE IF NOT EXISTS
  Machine_operations( 
    operation_id SERIAL PRIMARY KEY,
    machine_type INTEGER NOT NULL,
    tool INTEGER NOT NULL);

INSERT INTO
    Machine_operations (
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