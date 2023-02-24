BEGIN TRANSACTION;
DROP TABLE IF EXISTS `text_search_idx`;
CREATE TABLE IF NOT EXISTS `text_search_idx` (
	`segid`	TEXT,
	`term`	TEXT,
	`pgno`	TEXT,
	PRIMARY KEY(`segid`,`term`)
) WITHOUT ROWID;
DROP TABLE IF EXISTS `text_search_docsize`;
CREATE TABLE IF NOT EXISTS `text_search_docsize` (
	`id`	INTEGER,
	`sz`	BLOB,
	PRIMARY KEY(`id`)
);
DROP TABLE IF EXISTS `text_search_data`;
CREATE TABLE IF NOT EXISTS `text_search_data` (
	`id`	INTEGER,
	`block`	BLOB,
	PRIMARY KEY(`id`)
);
DROP TABLE IF EXISTS `text_search_content`;
CREATE TABLE IF NOT EXISTS `text_search_content` (
	`id`	INTEGER,
	`c0`	TEXT,
	`c1`	TEXT,
	PRIMARY KEY(`id`)
);
DROP TABLE IF EXISTS `text_search_config`;
CREATE TABLE IF NOT EXISTS `text_search_config` (
	`k`	TEXT,
	`v`	TEXT,
	PRIMARY KEY(`k`)
) WITHOUT ROWID;
DROP TABLE IF EXISTS `text_search`;
CREATE VIRTUAL TABLE text_search using fts5(memory_id,free_text);
DROP TABLE IF EXISTS `memories`;
CREATE TABLE IF NOT EXISTS `memories` (
	`memory_id`	INTEGER,
	`description`	TEXT NOT NULL,
	`text`	TEXT,
	`file_path`	TEXT,
	`unix_time`	integer,
	`public`	integer,
	`owner`	integer,
	`type`	text,
	PRIMARY KEY(`memory_id`)
);
DROP TABLE IF EXISTS `contacts`;
CREATE TABLE IF NOT EXISTS `contacts` (
	`contact_id`	INTEGER,
	`first_name`	TEXT NOT NULL,
	`last_name`	TEXT NOT NULL,
	`email`	TEXT NOT NULL UNIQUE,
	`phone`	TEXT NOT NULL UNIQUE,
	`logon`	INTEGER,
	PRIMARY KEY(`contact_id`)
);
DROP TABLE IF EXISTS `collage`;
CREATE TABLE IF NOT EXISTS `collage` (
	`collage_id`	INTEGER,
	`entry1`	TEXT,
	`entry2`	TEXT,
	`entry3`	TEXT,
	`entry4`	TEXT,
	`entry5`	TEXT,
	`entry6`	TEXT
);
COMMIT;
