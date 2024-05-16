CREATE TABLE IF NOT EXISTS
    Incoming(
        incoming_id SERIAL PRIMARY KEY,
        piece_type INTEGER NOT NULL,
        arrival_date INTEGER NOT NULL,
        piece_status varchar(20) NOT NULL,
        cost INTEGER NOT NULL,
        order_id INTEGER REFERENCES Orders(order_id)
    );