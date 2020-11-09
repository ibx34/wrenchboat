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
    "id" SERIAL, --BIGINT
    "type" VARCHAR,
    "target" BIGINT,
    "moderator" BIGINT,
    "reason" VARCHAR,
    "time_punsihed" TIMESTAMP,
    "guild" BIGINT,
    "modlogs" BIGINT
)