CREATE TABLE IF NOT EXISTS releases (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL
);

CREATE TABLE release_sellers (
    release_id INT NOT NULL,
    image_url TEXT,
    rating FLOAT,
    have INT,
    want INT,
    title TEXT,
    label TEXT,
    catno TEXT,
    media_condition TEXT,
    media_condition_description TEXT,
    seller TEXT,
    seller_rating FLOAT,
    ships_from TEXT,
    currency CHAR(3),
    price FLOAT,
    PRIMARY KEY (release_id, seller)
);

CREATE TABLE release_details (
    release_id INT PRIMARY KEY,
    have INT,
    want INT,
    avg_rating FLOAT,
    ratings INT,
    last_sold DATE,
    low FLOAT,
    median FLOAT,
    high FLOAT
);

CREATE TABLE release_wants (
    release_id INT,
    username TEXT,
    PRIMARY KEY (release_id, username)
);

CREATE TABLE release_haves (
    release_id INT,
    username TEXT,
    PRIMARY KEY (release_id, username)
);
