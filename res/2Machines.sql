CREATE TABLE IF NOT EXISTS Machines(
    machine_id SERIAL PRIMARY KEY,
    machine_type INTEGER REFERENCES Machine_tools(machine_type),
    Active_tool INTEGER,
    P1_count INTEGER,
    P2_count INTEGER,
    P3_count INTEGER,
    P4_count INTEGER,
    P5_count INTEGER,
    P6_count INTEGER,
    P7_count INTEGER,
    P8_count INTEGER,
    total_count INTEGER,
    operation_time INTEGER
);

INSERT INTO
    Machines (
        machine_id,
        machine_type,
        Active_tool,
        P1_count,
        P2_count,
        P3_count,
        P4_count,
        P5_count,
        P6_count,
        P7_count,
        P8_count,
        total_count,
        operation_time)
VALUES
    (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (3, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (4, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (5, 3, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (6, 3, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (7, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (8, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (9, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (10, 4, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (11, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (12, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);