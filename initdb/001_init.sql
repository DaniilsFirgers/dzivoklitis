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

-- create a table to store references to favourite flats
CREATE TABLE IF NOT EXISTS favourites(
    id SERIAL PRIMARY KEY, -- SERIAL is a type for auto-incrementing integers
    flat_id VARCHAR(255) NOT NULL,
    FOREIGN KEY(flat_id) REFERENCES flats(flat_id) ON DELETE CASCADE -- ON DELETE CASCADE means that if a flat is deleted, all references to it will be deleted as well
);

-- create indexes
CREATE INDEX idx_district ON flats(district);
CREATE INDEX idx_price ON prices(price);
CREATE INDEX idx_updated_at ON prices(updated_at);
CREATE INDEX idx_flat_id ON prices(flat_id);
CREATE INDEX idx_area ON flats(area);
create INDEX idx_flats_location ON flats USING GIST (location);

-- create composite index
CREATE INDEX idx_district_series ON flats(district, series);
-- create constraints
ALTER TABLE prices ADD CONSTRAINT chk_price CHECK (price > 0);
ALTER TABLE flats ADD CONSTRAINT chk_area CHECK (area > 0);
ALTER TABLE flats ADD CONSTRAINT chk_floor CHECK (floor <= floors_total);
ALTER TABLE flats ADD CONSTRAINT chk_rooms CHECK (rooms > 0);