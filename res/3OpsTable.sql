CREATE TABLE IF  NOT EXISTS OpsTable(
    op_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id) NOT NULL,
    op_1 INTEGER REFERENCES Available_transforms(id) NOT NULL,
    op_2 INTEGER REFERENCES Available_transforms(id),
    ops_status VARCHAR(255) NOT NULL
);