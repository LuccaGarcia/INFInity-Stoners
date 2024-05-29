CREATE TABLE IF NOT EXISTS Lines(
    line_id SERIAL PRIMARY KEY,
    machine_A INTEGER REFERENCES Machines(machine_id),
    machine_B INTEGER REFERENCES Machines(machine_id)
);

INSERT INTO
    Lines (
        line_id,
        machine_A,
        machine_B)
VALUES
    (1, 1, 7),
    (2, 2, 8),
    (3, 3, 9),
    (4, 4, 10),
    (5, 5, 11),
    (6, 6, 12);