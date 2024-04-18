CREATE TABLE IF NOT EXISTS Pieces(
    piece_id SERIAL PRIMARY KEY,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    piece_type INTEGER NOT NULL,
    accumulated_cost INTEGER
);