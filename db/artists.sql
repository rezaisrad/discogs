CREATE TABLE artist_aliases (
    artist_id INTEGER NOT NULL,
    alias_id INTEGER NOT NULL,
    alias_name TEXT NOT NULL,
    PRIMARY KEY (artist_id, alias_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

CREATE TABLE artist_groups (
    artist_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    PRIMARY KEY (artist_id, group_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

CREATE TABLE artist_name_variations (
    artist_id INTEGER NOT NULL,
    name_variation VARCHAR(255),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

CREATE TABLE artist_websites (
    artist_id INTEGER NOT NULL,
    url TEXT,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);


INSERT INTO artist_websites (artist_id, url)
SELECT
    a.artist_id,
    jsonb_array_elements(a.data->'urls') AS url
FROM
    artists a;

INSERT INTO artist_name_variations (artist_id, name_variation)
SELECT
    a.artist_id,
    jsonb_array_elements(a.data->'namevariations') AS name_variation
FROM
    artists a;

INSERT INTO artist_aliases (artist_id, alias_id, alias_name)
SELECT
    a.artist_id,
    CAST(jsonb_array_elements(a.data->'aliases')->>'id' AS INTEGER) AS alias_id,
    jsonb_array_elements(a.data->'aliases')->>'name' AS alias_name
FROM
    artists a;
	
INSERT INTO artist_groups (artist_id, group_id, group_name)
SELECT
    a.artist_id,
    CAST(jsonb_array_elements(a.data->'groups')->>'id' AS INTEGER) AS group_id,
    jsonb_array_elements(a.data->'groups')->>'name' AS group_name
FROM
    artists a;
	
ALTER TABLE public.artists ADD COLUMN name VARCHAR(255);
ALTER TABLE public.artists ADD COLUMN real_name VARCHAR(255);
ALTER TABLE public.artists ADD COLUMN description TEXT;

UPDATE artists 
SET name = data->>'name';

UPDATE artists 
SET description = data->>'profile';

UPDATE artists 
SET real_name = data->>'real_name';
