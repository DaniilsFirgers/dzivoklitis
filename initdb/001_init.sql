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
    city VARCHAR(50) NOT NULL,
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

CREATE TABLE IF NOT EXISTS filters (
    id SERIAL PRIMARY KEY,
    deal_type VARCHAR(30) NOT NULL,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    room_range NUMRANGE NOT NULL,
    price_range NUMRANGE NOT NULL,
    area_range NUMRANGE NOT NULL,
    floor_range NUMRANGE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    tg_user_id BIGINT NOT NULL,
    FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS price_trends (
    id SERIAL PRIMARY KEY,
    flat_id VARCHAR(255) NOT NULL,
    current_price INT NOT NULL,
    initial_price INT NOT NULL,
    price_diff INT NOT NULL,
    pct_change NUMERIC(5, 2) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'weekly', 'monthly', or 'quarterly'
    start_time TIMESTAMPTZ NOT NULL,  -- Start of the period
    end_time TIMESTAMPTZ NOT NULL,    -- End of the period
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (flat_id) REFERENCES flats(flat_id) ON DELETE CASCADE
);


-- create indexes
CREATE INDEX idx_price_flat_id ON prices(flat_id);
CREATE INDEX idx_price_flat_id_price ON prices(flat_id, price);
CREATE INDEX idx_prices_flat_id_updated_at ON prices(flat_id, updated_at);
CREATE INDEX idx_fav_flat_id ON favourites(flat_id);
CREATE INDEX idx_fav_tg_user_id ON favourites(tg_user_id);
CREATE INDEX idx_user_tg_user_id ON users(tg_user_id);
create INDEX idx_flat_location ON flats USING GIST (location);
CREATE INDEX idx_city_district ON filters (city, deal_type, district);
CREATE INDEX idx_trends_type_end_time_start_time ON price_trends(type, start_time, end_time);

-- create constraints
ALTER TABLE prices ADD CONSTRAINT price_check CHECK (price > 0);
ALTER TABLE flats ADD CONSTRAINT area_check CHECK (area > 0);
ALTER TABLE flats ADD CONSTRAINT floors_total_check CHECK (floors_total > 0);
ALTER TABLE flats ADD CONSTRAINT rooms_check CHECK (rooms > 0);
ALTER TABLE flats ADD CONSTRAINT floor_vs_total_floor_check CHECK (floor <= floors_total);
ALTER TABLE flats ADD CONSTRAINT floor_check CHECK (floor > 0);
ALTER TABLE favourites ADD CONSTRAINT uq_fav_flat_id_tg_user_id UNIQUE (flat_id, tg_user_id);
ALTER TABLE users ADD CONSTRAINT uq_user_tg_user_id UNIQUE (tg_user_id);

-- Add constraints for the `filters` table
ALTER TABLE filters ADD CONSTRAINT room_range_not_null CHECK (room_range IS NOT NULL);
ALTER TABLE filters ADD CONSTRAINT price_range_not_null CHECK (price_range IS NOT NULL);
ALTER TABLE filters ADD CONSTRAINT area_range_not_null CHECK (area_range IS NOT NULL);
ALTER TABLE filters ADD CONSTRAINT floor_range_not_null CHECK (floor_range IS NOT NULL);
ALTER TABLE filters ADD CONSTRAINT check_room_range CHECK (lower(room_range) <= upper(room_range));
ALTER TABLE filters ADD CONSTRAINT check_price_range CHECK (lower(price_range) <= upper(price_range));
ALTER TABLE filters ADD CONSTRAINT check_area_range CHECK (lower(area_range) <= upper(area_range));
ALTER TABLE filters ADD CONSTRAINT check_floor_range CHECK (lower(floor_range) <= upper(floor_range));
ALTER TABLE filters ADD CONSTRAINT uq_city_district UNIQUE (city, deal_type, district);