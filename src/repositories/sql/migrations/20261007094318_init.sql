-- migrate:up
CREATE EXTENSION IF NOT EXISTS "pg_idkit";

CREATE TABLE conversations (
  id VARCHAR(26) PRIMARY KEY DEFAULT idkit_ulid_generate(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  guild_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,

  UNIQUE (guild_id, channel_id)
);
CREATE INDEX conversations_channel_id_ix ON conversations (channel_id);

CREATE TYPE CHAT_ROLE AS ENUM ('user', 'assistant', 'system');

CREATE TABLE messages (
  id VARCHAR(26) NOT NULL DEFAULT idkit_ulid_generate(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  conversation_id VARCHAR(26) NOT NULL,
  chat_role CHAT_ROLE NOT NULL,
  content TEXT NOT NULL,
  author_id BIGINT,

  CONSTRAINT messages_id_pk PRIMARY KEY (id),
  CONSTRAINT conversation_id_fk FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE,
  CHECK (
    (author_id IS NULL AND chat_role != 'user')
    OR (author_id IS NOT NULL AND chat_role = 'user')
  )
);
CREATE INDEX messages_id_ix ON messages (id);
CREATE INDEX messages_conversation_id_ix ON messages (conversation_id);

-- migrate:down
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversations;
DROP TYPE IF EXISTS CHAT_ROLE;
