CREATE TABLE IF NOT EXISTS
  Machine_tools( 
    machine_type SERIAL PRIMARY KEY,
    t1 INTEGER NOT NULL,
    t2 INTEGER NOT NULL,
    t3 INTEGER NOT NULL);

INSERT INTO
    Machine_tools (
        machine_type,
        t1,
        t2,
        t3)
VALUES
    (1, 1, 2, 3),
    (2, 1, 2, 3),
    (3, 1, 4, 5),
    (4, 1, 4, 6);