CREATE TABLE IF NOT EXISTS
    TrafficPieces( 
        id SERIAL PRIMARY KEY,
        piece_id INTEGER REFERENCES Pieces(piece_id),
        line_id INTEGER NOT NULL
    );

