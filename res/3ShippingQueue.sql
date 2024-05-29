CREATE TABLE IF NOT EXISTS ShippingQueue(
    shipping_id SERIAL PRIMARY KEY,
    piece_id INTEGER REFERENCES Pieces(piece_id) NOT NULL,
    order_id INTEGER REFERENCES Orders(order_id) NOT NULL,
    shipping_line INTEGER
);