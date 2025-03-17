-- Enable PostGIS for working with geospatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create a flats table
-- By default the columns are NULL, if not specified otherwise, or default is set
-- use a composite type for address
CREATE TABLE IF NOT EXISTS flats(
    flat_id VARCHAR(255) PRIMARY KEY, -- VARCHAR is a string with a maximum length of 255 characters
    source VARCHAR(30) NOT NULL, -- where the flat was found
    deal_type VARCHAR(30) NOT NULL, -- sale or rent
    url TEXT NOT NULL, -- TEXT is a type for long strings
    district VARCHAR(100) NOT NULL, -- VARCHAR is a shorthand for VARCHAR(255), which is a string with a maximum length of 255 characters
    city VARCHAR(100) NOT NULL,
    street VARCHAR(150) NOT NULL,
    rooms SMALLINT NOT NULL, -- SMALLINT is a type for small integers
    floors_total SMALLINT NOT NULL, -- how many floors are in the building
    floor SMALLINT NOT NULL, -- on which floor the flat is located
    area DECIMAL(5, 2) NOT NULL, -- DECIMAL is a type for numbers with a fixed number of digits before and after the decimal point
    series TEXT NOT NULL, -- series of the building
    location GEOMETRY(POINT, 4326), -- GEOMETRY is a type for geospatial data to store coordinates
    image_data BYTEA DEFAULT ''::bytea, -- BYTEA is a type for binary data
    created_at TIMESTAMPTZ DEFAULT NOW() -- also can use CURRENT_TIMESTAMP for default value
);

-- create a table to store price updates
CREATE TABLE IF NOT EXISTS prices(
    id SERIAL PRIMARY KEY,
    flat_id VARCHAR(255) NOT NULL,
    FOREIGN KEY(flat_id) REFERENCES flats(flat_id) ON DELETE CASCADE,
    price INT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(30),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- create a table to store references to favourite flats
CREATE TABLE IF NOT EXISTS favourites(
    id SERIAL PRIMARY KEY, -- SERIAL is a type for auto-incrementing integers
    flat_id VARCHAR(255) NOT NULL,
    tg_user_id BIGINT NOT NULL,
    FOREIGN KEY(flat_id) REFERENCES flats(flat_id) ON DELETE CASCADE, -- ON DELETE CASCADE means that if a flat is deleted, all references to it will be deleted as well
    FOREIGN KEY(tg_user_id) REFERENCES users(tg_user_id) ON DELETE CASCADE
);

-- create indexes
CREATE INDEX idx_price_flat_id ON prices(flat_id);
CREATE INDEX idx_price_flat_id_price ON prices(flat_id, price);
CREATE INDEX idx_fav_flat_id ON favourites(flat_id);
CREATE INDEX idx_fav_tg_user_id ON favourites(tg_user_id);
CREATE INDEX idx_user_tg_user_id ON users(tg_user_id);
create INDEX idx_flat_location ON flats USING GIST (location);

-- create constraints
ALTER TABLE prices ADD CONSTRAINT price_check CHECK (price > 0);
ALTER TABLE flats ADD CONSTRAINT area_check CHECK (area > 0);
ALTER TABLE flats ADD CONSTRAINT floors_total_check CHECK (floors_total > 0);
ALTER TABLE flats ADD CONSTRAINT rooms_check CHECK (rooms > 0);
ALTER TABLE flats ADD CONSTRAINT floor_vs_total_floor_check CHECK (floor <= floors_total);
ALTER TABLE flats ADD CONSTRAINT floor_check CHECK (floor > 0);
ALTER TABLE favourites ADD CONSTRAINT uq_fav_flat_id_tg_user_id UNIQUE (flat_id, tg_user_id);
ALTER TABLE users ADD CONSTRAINT uq_user_tg_user_id UNIQUE (tg_user_id);