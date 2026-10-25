DROP TABLE IF EXISTS observations;

CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    observation_date DATE NOT NULL,
    water_clarity_score INTEGER NOT NULL CHECK (water_clarity_score BETWEEN 1 AND 5),
    litter_count INTEGER NOT NULL CHECK (litter_count >= 0),
    vegetation_cover_pct REAL NOT NULL CHECK (vegetation_cover_pct BETWEEN 0 AND 100),
    odor_score INTEGER NOT NULL CHECK (odor_score BETWEEN 0 AND 5),
    visible_algae INTEGER NOT NULL CHECK (visible_algae IN (0,1)),
    nearby_urban_pressure TEXT NOT NULL CHECK (nearby_urban_pressure IN ('low','medium','high')),
    notes TEXT
);
