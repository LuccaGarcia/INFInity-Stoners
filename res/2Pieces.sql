CREATE TABLE IF NOT EXISTS Pieces(
    piece_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES Orders(order_id),
    current_piece_type INTEGER NOT NULL,
    final_piece_type INTEGER,
    accumulated_cost INTEGER,
    accumulated_time INTEGER
);
