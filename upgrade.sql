-- begin;
-- ALTER TABLE users ADD COLUMN last_seen TEXT;
-- PRAGMA user_version = 1;
-- commit;

begin;
alter table keys add column allocated bool;
update keys set allocated = 0;
pragma user_version = 2;
commit;
