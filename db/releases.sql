SELECT id
FROM electronic_releases
WHERE id IN (SELECT release_id FROM release_styles WHERE style IN ('House', 'Techno', 'Electro', 'Trance', 'Tech House', 'Deep House', 'Progressive House', 'Minimal', 'Breakbeat', 'Progressive Trance', 'Breaks', 'Electro House', 'Acid', 'Jungle', 'Garage House', 'UK Garage', 'Dub Techno', 'Acid House', 'Minimal Techno', 'Freestyle', 'Acid Jazz', 'Lo-Fi', 'Tribal House', 'Deep Techno', 'Hip-House', 'Italo House'))
AND id IN (SELECT release_id FROM release_formats WHERE format_name = 'Vinyl')
AND release_date BETWEEN '1975-01-01' AND '2010-01-01'
ORDER BY id
LIMIT 50