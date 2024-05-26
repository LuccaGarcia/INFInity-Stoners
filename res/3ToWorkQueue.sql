CREATE TABLE IF NOT EXISTS ToWorkQueue(
    work_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id)
);