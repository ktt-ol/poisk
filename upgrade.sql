begin;
ALTER TABLE users ADD COLUMN last_seen TEXT;
PRAGMA user_version = 1;
commit;
