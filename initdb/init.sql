-- Create a flats table
-- By default the columns are NULL, if not specified otherwise, or default is set
-- use a composite type for address
CREATE TABLE IF NOT EXISTS flats(
    flat_id VARCHAR(255) PRIMARY KEY, -- VARCHAR is a string with a maximum length of 255 characters
    source VARCHAR(30) NOT NULL, -- where the flat was found
    link TEXT NOT NULL, -- TEXT is a type for long strings
    district VARCHAR(100) NOT NULL, -- VARCHAR is a shorthand for VARCHAR(255), which is a string with a maximum length of 255 characters
    street VARCHAR(150) NOT NULL,
    rooms SMALLINT NOT NULL, -- SMALLINT is a type for small integers
    floors_total SMALLINT NOT NULL, -- how many floors are in the building
    floor SMALLINT NOT NULL, -- on which floor the flat is located
    price_per_m2 FLOAT NOT NULL, -- FLOAT can make rounding errors, but we will use it
    area DECIMAL(5, 2) NOT NULL, -- DECIMAL is a type for numbers with a fixed number of digits before and after the decimal point
    series TEXT NOT NULL, -- series of the building
    updated_at TIMESTAMPTZ DEFAULT NOW(), -- TIMESTAMPTZ is a type for timestamps with time zone
    created_at TIMESTAMPTZ DEFAULT NOW() -- also can use CURRENT_TIMESTAMP for default value
);

-- create a table to store references to favourite flats
CREATE TABLE IF NOT EXISTS favourite_flats(
    id SERIAL PRIMARY KEY, -- SERIAL is a type for auto-incrementing integers
    flat_id VARCHAR(255) NOT NULL,
    FOREIGN KEY(flat_id) REFERENCES flats(flat_id) ON DELETE CASCADE -- ON DELETE CASCADE means that if a flat is deleted, all references to it will be deleted as well
);

-- create a link table to trace relationships between flat adds that were updated
CREATE TABLE IF NOT EXISTS flat_updates(
    flat_1_id VARCHAR(255) NOT NULL,
    flat_2_id VARCHAR(255) NOT NULL,
    PRIMARY KEY(flat_1_id, flat_2_id),
    FOREIGN KEY(flat_1_id) REFERENCES flats(flat_id) ON DELETE CASCADE, -- foreign key is a reference to another table
    FOREIGN KEY(flat_2_id) REFERENCES flats(flat_id) ON DELETE CASCADE -- ON DELETE CASCADE means that if a flat is deleted, all references to it will be deleted as well
);

-- create indexes
CREATE INDEX idx_district ON flats(district);
CREATE INDEX idx_price_per_m2 ON flats(price_per_m2);
CREATE INDEX idx_area ON flats(area);
-- create composite index
CREATE INDEX idx_district_price_per_m2 ON flats(district, price_per_m2);
-- create constraints
ALTER TABLE flats ADD CONSTRAINT chk_price_per_m2 CHECK (price_per_m2 > 0);
ALTER TABLE flats ADD CONSTRAINT chk_area CHECK (area > 0);
ALTER TABLE flats ADD CONSTRAINT chk_floor CHECK (floor <= floors_total);
ALTER TABLE flats ADD CONSTRAINT chk_rooms CHECK (rooms > 0);