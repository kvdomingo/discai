-- name: GetConversationById :one
SELECT *
FROM conversations
WHERE id = $1;

-- name: GetConversationByGuildChannelId :one
SELECT *
FROM conversations
WHERE
  guild_id = $1
  AND channel_id = $2;

-- name: CreateConversation :one
INSERT INTO conversations (guild_id, channel_id)
VALUES ($1, $2)
ON CONFLICT (guild_id, channel_id) DO NOTHING
RETURNING *;
