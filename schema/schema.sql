sqlite> .schema
.schema
CREATE TABLE contacts (
contact_id INTEGER PRIMARY KEY,
first_name TEXT NOT NULL,
last_name TEXT NOT NULL,
email TEXT NOT NULL UNIQUE,
phone TEXT NOT NULL UNIQUE
);
CREATE TABLE memories (
memory_id INTEGER PRIMARY KEY,
description TEXT NOT NULL,
text TEXT,
file_path TEXT,
unix_time integer,
    public integer
, owner integer, type text);

CREATE VIRTUAL TABLE text_search using fts5(memory_id,free_text)
/* text_search(memory_id,free_text) */;
CREATE TABLE IF NOT EXISTS 'text_search_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'text_search_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'text_search_content'(id INTEGER PRIMARY KEY, c0, c1);
CREATE TABLE IF NOT EXISTS 'text_search_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'text_search_config'(k PRIMARY KEY, v) WITHOUT ROWID;

