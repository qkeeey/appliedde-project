CREATE TABLE IF NOT EXISTS hosts (
    host_id BIGINT PRIMARY KEY,
    host_name TEXT,
    calculated_host_listings_count INT
);

CREATE TABLE IF NOT EXISTS locations (
    location_id SERIAL PRIMARY KEY,
    neighbourhood_group TEXT,
    neighbourhood TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);

CREATE TABLE IF NOT EXISTS listings (
    listing_id BIGINT PRIMARY KEY,
    name TEXT,
    host_id BIGINT REFERENCES hosts(host_id),
    location_id INT REFERENCES locations(location_id),
    room_type TEXT,
    price NUMERIC,
    minimum_nights INT
);

CREATE TABLE IF NOT EXISTS reviews (
    listing_id BIGINT PRIMARY KEY REFERENCES listings(listing_id),
    number_of_reviews INT,
    last_review DATE,
    reviews_per_month NUMERIC
);

CREATE TABLE IF NOT EXISTS availability (
    listing_id BIGINT PRIMARY KEY REFERENCES listings(listing_id),
    availability_365 INT
);

CREATE INDEX IF NOT EXISTS idx_listings_host_id ON listings(host_id);
CREATE INDEX IF NOT EXISTS idx_listings_location_id ON listings(location_id);
CREATE INDEX IF NOT EXISTS idx_locations_neighbourhood ON locations(neighbourhood);
CREATE INDEX IF NOT EXISTS idx_listings_room_type ON listings(room_type);