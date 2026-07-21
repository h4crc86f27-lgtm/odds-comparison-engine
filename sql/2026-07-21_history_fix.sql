-- 2026-07-21
-- Fix Betfair history processing

ALTER TABLE processed_historical
MODIFY odds LONGTEXT NOT NULL;

CREATE INDEX idx_timestamp
ON odds_history(timestamp);

CREATE INDEX idx_matchid_market
ON processed_historical(matchid(100), market(100));
