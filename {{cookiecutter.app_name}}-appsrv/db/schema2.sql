/**
* {{cookiecutter.app_name}} Database Schema
*
* Core functionality:
**/

CREATE TABLE users (
	id               bigserial PRIMARY KEY,
	username         text NOT NULL,
	email            varchar(254) NOT NULL,                    -- http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
	password         text NOT NULL,                            -- SHA-512 hash of <password, salt>
	salt             text NOT NULL,                            -- big 'ol pile of entropy
	created          timestamp DEFAULT current_timestamp
);

CREATE TABLE sessions (
	id               bigserial PRIMARY KEY,
	user_id          bigint REFERENCES pj.users(id),
	started          timestamp default current_timestamp,
	lastactive       timestamp default current_timestamp,
	token            text NOT NULL
);
