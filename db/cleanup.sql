
CREATE TABLE electronic_releases (
    id INT PRIMARY KEY,
    data JSONB
);

DROP TABLE releases;

INSERT INTO electronic_releases (id, data)
SELECT (data->>'id')::INT AS id,
       data
FROM releases
WHERE data->'genres' ? 'Electronic';


ALTER TABLE electronic_releases ADD COLUMN master_id BOOLEAN;

UPDATE electronic_releases
SET master_id = CASE
    WHEN data->>'master_id' = 'true' THEN True
    WHEN data->>'master_id' = 'false' THEN False
    ELSE NULL
END;


ALTER TABLE electronic_releases ADD COLUMN release_date TEXT;

CREATE OR REPLACE FUNCTION parse_release_date(release_text TEXT) RETURNS DATE AS $$
DECLARE
    parsed_date DATE;
BEGIN
    -- Handle YYYY-MM-DD format, replacing "00" with valid default values
    parsed_date := TO_DATE(NULLIF(regexp_replace(release_text, '-00', '', 'g'), ''), 'YYYY-MM-DD');
    
    -- Fallback to YYYY-MM if DD is missing or "00"
    IF parsed_date IS NULL THEN
        parsed_date := TO_DATE(NULLIF(regexp_replace(release_text, '-00$', '', 'g'), ''), 'YYYY-MM');
    END IF;
    
    -- Fallback to YYYY if MM is missing or "00"
    IF parsed_date IS NULL THEN
        parsed_date := TO_DATE(release_text, 'YYYY');
    END IF;
    
    RETURN parsed_date;
END;
$$ LANGUAGE plpgsql;

UPDATE electronic_releases
SET release_date = parse_release_date(data->>'released');

CREATE TABLE release_labels (
    release_id TEXT NOT NULL,
    label_id TEXT,
    label_name TEXT,
    catno TEXT
);

INSERT INTO release_labels (release_id, label_id, label_name, catno)
SELECT
    er.data->>'id' AS release_id,
    jsonb_label->>'id' AS label_id,
    jsonb_label->>'name' AS label_name,
    jsonb_label->>'catno' AS catno
FROM
    electronic_releases er,
    jsonb_array_elements(er.data->'labels') AS jsonb_label;

CREATE TABLE release_videos (
    release_id TEXT NOT NULL,
    video_src TEXT,
    video_title TEXT,
    video_description TEXT
);

INSERT INTO release_videos (release_id, video_src, video_title, video_description)
SELECT
    er.data->>'id' AS release_id,
    jsonb_video->>'src' AS video_src,
    jsonb_video->>'title' AS video_title,
    jsonb_video->>'description' AS video_description
FROM
    electronic_releases er,
    jsonb_array_elements(er.data->'videos') AS jsonb_video;

CREATE TABLE release_artists (
    release_id INT NOT NULL,
    artist_id TEXT,
    artist_name TEXT
);

INSERT INTO release_artists (release_id, artist_id, artist_name)
SELECT
    er.id AS release_id,
    jsonb_artist->>'id' AS artist_id,
    jsonb_artist->>'name' AS artist_name
FROM
    electronic_releases er,
    jsonb_array_elements(er.data->'artists') AS jsonb_artist;

CREATE TABLE release_formats (
    release_id INT NOT NULL,
    qty INT,
    format_name TEXT,
    descriptions JSONB
);

INSERT INTO release_formats (release_id, qty, format_name, descriptions)
SELECT
    er.id AS release_id,
    (jsonb_format->>'qty')::INT AS qty,
    jsonb_format->>'name' AS format_name,
    jsonb_format->'descriptions' AS descriptions
FROM
    electronic_releases er,
    jsonb_array_elements(er.data->'formats') AS jsonb_format;

ALTER TABLE release_formats
ADD CONSTRAINT fk_release_formats_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_artists
ADD CONSTRAINT fk_release_artists_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_labels
ADD CONSTRAINT fk_release_labels_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_companies
ADD CONSTRAINT fk_release_companies_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_styles
ADD CONSTRAINT fk_release_styles_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_tracklist
ADD CONSTRAINT fk_release_tracklist_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);

ALTER TABLE release_videos
ADD CONSTRAINT fk_release_videos_release_id
FOREIGN KEY (release_id) REFERENCES electronic_releases(id);
