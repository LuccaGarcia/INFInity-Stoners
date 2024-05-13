CREATE TABLE IF NOT EXISTS
  Warehouse( 
    id SERIAL PRIMARY KEY,
    Warehouse INTEGER NOT NULL,
    piece_id INTEGER REFERENCES Pieces(piece_id),
    piece_type INTEGER NOT NULL,
    piece_status VARCHAR(255) NOT NULL
  );
