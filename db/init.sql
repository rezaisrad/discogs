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


ALTER TABLE release_sellers ADD COLUMN created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE release_details ADD COLUMN created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE release_wants ADD COLUMN created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE release_haves ADD COLUMN created_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE release_wants
ADD CONSTRAINT fk_release_wants_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_haves
ADD CONSTRAINT fk_release_haves_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_sellers
ADD CONSTRAINT fk_release_sellers_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_details
ADD CONSTRAINT fk_release_details_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

DELETE FROM artists
USING release_artists
WHERE artists.artist_id = release_artists.artist_id
AND release_artists.artist_id IS NULL;
