INSERT INTO flats (
    flat_id,
    source,
    url,
    district,
    street,
    rooms,
    floors_total,
    floor,
    area,
    series,
    location,
    image_data
) VALUES (
    '07de7d82117765eac419e02a8d4d9c7b', -- Unique ID for the flat
    'ss', -- Source of the flat listing
    'https://www.ss.lv//msg/lv/real-estate/flats/riga/imanta/beomxi.html', -- URL of the flat listing
    'imanta', -- District of the flat
    'Anniņmuižas 40E', -- Street where the flat is located
    2, -- Number of rooms
    5, -- Total number of floors in the building
    4, -- Floor on which the flat is located
    50.00, -- Area of the flat in square meters
    'LT proj.', -- Series of the building
    ST_SetSRID(ST_MakePoint(56.9607, 24.0103), 4326), -- Geographical location (longitude, latitude)
    ''::bytea -- Binary data for images (empty in this case)
);

INSERT INTO flats_price (flat_id, price_per_m2) 
VALUES ('07de7d82117765eac419e02a8d4d9c7b', 900);