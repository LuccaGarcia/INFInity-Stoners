CREATE TABLE IF NOT EXISTS Machines(
    machine_id SERIAL PRIMARY KEY,
    FOREIGN KEY (machine_type) REFERENCES Machine_operations(machine_type),
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