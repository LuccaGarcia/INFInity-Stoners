CREATE TABLE IF NOT EXISTS Transformations(
    trasformation_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id),
    start_piece_type INTEGER NOT NULL,
    end_piece_type INTEGER NOT NULL,
    operation_id INTEGER REFERENCES Operations(operation_id)
);
