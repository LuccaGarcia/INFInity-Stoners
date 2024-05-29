CREATE TABLE IF NOT EXISTS Orders(
    order_id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    order_number INTEGER NOT NULL,
    final_piece_type INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    placement_date INTEGER NOT NULL,
    due_date INTEGER NOT NULL,
    late_penalty INTEGER NOT NULL,
    early_penalty INTEGER NOT NULL,
    delivery_date INTEGER,
    delivery_status VARCHAR(255),
    final_cost INTEGER
);