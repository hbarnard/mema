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
