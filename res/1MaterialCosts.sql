CREATE TABLE IF NOT EXISTS
  MaterialCosts( 
    id SERIAL PRIMARY KEY,
    supplier INTEGER NOT NULL,
    piece INTEGER NOT NULL,
    min_order INTEGER NOT NULL,
    price_per_piece INTEGER NOT NULL,
    delivery_time INTEGER NOT NULL);

INSERT INTO
    MaterialCosts (
        supplier,
        piece,
        min_order,
        price_per_piece,
        delivery_time)
VALUES
    (1, 1, 16, 30, 4),
    (1, 2, 16, 30, 4),
    (2, 1,  8, 45, 2),
    (2, 2,  8, 15, 2),
    (3, 1,  4, 55, 1),
    (3, 2,  4, 18, 1);

