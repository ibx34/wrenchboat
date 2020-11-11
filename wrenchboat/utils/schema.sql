CREATE TABLE
IF NOT EXISTS guilds
(
    "id" BIGINT,
    "prefix" VARCHAR,
    "prefixes" VARCHAR[] DEFAULT '{}',
    "muterole" BIGINT,
    "dontmute" BIGINT,
    "modlogs" BIGINT,
    "antiprofanity" VARCHAR,
    "antihoist" BOOLEAN DEFAULT FALSE, --VARCHAR
    "modrole" BIGINT
);

CREATE TABLE
IF NOT EXISTS infractions
(
    "id" BIGINT, --SERIAL
    "type" VARCHAR,
    "target" BIGINT,
    "moderator" BIGINT,
    "reason" VARCHAR,
    "time_punsihed" TIMESTAMP,
    "guild" BIGINT,
    "modlogs" BIGINT
);

CREATE TABLE 
IF NOT EXISTS tags
(
    "id" SERIAL,
    "name" VARCHAR,
    "content" VARCHAR,
    "author" BIGINT,
    "guild" BIGINT,
    "created" TIMESTAMP,
    "uses" BIGINT DEFAULT 0
);

CREATE TABLE 
IF NOT EXISTS user_backups
(
    "id" SERIAL,
    "target" BIGINT,
    "roles" BIGINT[] DEFAULT '{}'
)