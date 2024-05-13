CREATE TABLE IF NOT EXISTS Pieces(
    piece_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES Orders(order_id),
    piece_type INTEGER NOT NULL,
    accumulated_cost INTEGER
);