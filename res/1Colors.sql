CREATE TABLE IF NOT EXISTS
  Colors( 
    piece_type INTEGER PRIMARY KEY,
    color VARCHAR(255) NOT NULL);

INSERT INTO
    Colors (
        piece_type,
        color)
VALUES
    (1, 'Brown'),
    (2, 'Red'),
    (3, 'Orenge'),
    (4, 'yellow'),
    (5, 'Green'),
    (6, 'Blue'),
    (7, 'Violet'),
    (8, 'Gray'),
    (9, 'White');