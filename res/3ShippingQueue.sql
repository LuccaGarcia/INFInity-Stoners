CREATE TABLE IF NOT EXISTS ShippingQueue(
    shipping_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id)
);