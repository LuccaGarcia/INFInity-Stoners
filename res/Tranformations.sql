CREATE TABLE IF NOT EXISTS Transformations(
    trasformation_id SERIAL PRIMARY KEY,
    FOREIGN KEY (piece_id) REFERENCES Pieces(piece_id),
    start_piece_type INTEGER NOT NULL,
    end_piece_type INTEGER NOT NULL,
    FOREIGN KEY (operation_id) REFERENCES Machine_operations(operation_id)
);
