CREATE TABLE
IF NOT EXISTS guilds
(
    "id" BIGINT,
    "prefix" VARCHAR,
    "prefixes" VARCHAR[] DEFAULT '{"wrench","w!"}',
    "muterole" BIGINT,
    "dontmute" BIGINT,
    "modlogs" BIGINT,
    "messagelogs" BIGINT,
    "userlogs" BIGINT,
    "automodlogs" BIGINT,
    "serverlogs" BIGINT,
    "archive_category" BIGINT,
    "antiprofanity" VARCHAR,
    "antihoist" BOOLEAN DEFAULT FALSE, --VARCHAR
    "antinvite" VARCHAR, 
    "antiraid" VARCHAR,
    "antimassping" VARCHAR,
    "antispam" VARCHAR,
    "antiping" VARCHAR,
    "antiemojispam" VARCHAR,
    "token_remover" BOOLEAN DEFAULT FALSE,
    "modrole" BIGINT,
    "starboard_channel" BIGINT,
    "needed_stars" BIGINT DEFAULT 3,
    "self_starring" BOOLEAN DEFAULT FALSE,
    "language" VARCHAR DEFAULT "en",
    "global_bans" BOOLEAN DEFAULT FALSE,
    "response_type" VARCHAR DEFAULT 'advanced',
    "anti_ping_list" BIGINT[] DEFAULT '{}'
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
    "modlogs" BIGINT,
    "roles" BIGINT[] DEFAULT '{}'
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
    "roles" BIGINT[] DEFAULT '{}',
    "guild" BIGINT
);

CREATE TABLE 
IF NOT EXISTS starboard
(
    "guild" BIGINT,
    "starboard_message" BIGINT,
    "attachment" VARCHAR,
    "origin_message" BIGINT,
    "author" BIGINT,
    "stars" BIGINT
);

CREATE TABLE
IF NOT EXISTS highlights 
(
    "guild" BIGINT,
    "author" BIGINT,
    "id" SERIAL,
    "phrase" VARCHAR
);

CREATE TABLE
IF NOT EXISTS notes
(
    "id" SERIAL,
    "guild" BIGINT,
    "author" BIGINT,
    "target" BIGINT,
    "content" VARCHAR,
    "time_given" TIMESTAMP
);

CREATE TABLE
IF NOT EXISTS archived_channels 
(
    "id" SERIAL,
    "channel" BIGINT,
    "category" BIGINT,
    "position" BIGINT
)