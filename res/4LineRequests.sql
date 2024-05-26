CREATE TABLE IF NOT EXISTS LineRequests(
    request_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id) NOT NULL,
    op_id INTEGER REFERENCES OpsTable(op_id) NOT NULL,
    lines VARCHAR(255) NOT NULL,
    n_ops INTEGER NOT NULL
)