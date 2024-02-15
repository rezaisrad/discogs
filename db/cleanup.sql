CREATE TABLE electronic_releases (
    id INT PRIMARY KEY,
    data JSONB
);

INSERT INTO electronic_releases (id, data)
SELECT (data->>'id')::INT AS id,
       data
FROM releases
WHERE data->'genres' ? 'Electronic';

DROP TABLE releases;