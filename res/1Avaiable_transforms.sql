CREATE TABLE IF NOT EXISTS
  Available_transforms( 
    id SERIAL PRIMARY KEY,
    start_piece_type INTEGER NOT NULL,
    end_piece_type INTEGER NOT NULL,
    tool INTEGER NOT NULL,
    processing_time INTEGER NOT NULL );

INSERT INTO
  Available_transforms (
    start_piece_type,
    end_piece_type,
    tool,
    processing_time)
VALUES
  ( 1, 3, 1, 45),
  ( 3, 4, 2, 15),
  -- ( 3, 4, 3, 25),
  ( 4, 5, 4, 25),
  ( 4, 6, 2, 25),
  -- ( 4, 7, 3, 15),
  ( 2, 8, 1, 45),
  ( 8, 7, 6, 15),
  ( 8, 9, 5, 45);



 