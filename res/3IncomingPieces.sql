CREATE TABLE IF NOT EXISTS
    Incoming(
        piece_id SERIAL PRIMARY KEY,
        piece_type INTEGER NOT NULL,
        arrival_date INTEGER NOT NULL,
        piece_status varchar(20) NOT NULL,
        cost INTEGER NOT NULL
    );