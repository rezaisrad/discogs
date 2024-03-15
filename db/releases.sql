SELECT DISTINCT release_id
FROM release_sellers_backup
WHERE release_id NOT IN (SELECT release_id FROM release_sellers)