-- name: GetMessage :one
SELECT *
FROM messages
WHERE id = $1;

-- name: ListMessagesInConversation :many
SELECT m.*
FROM messages m
JOIN conversations c
  ON c.id = m.conversation_id
  AND c.id = $1
ORDER BY
  m.created_at,
  CASE m.chat_role
    WHEN 'system'::CHAT_ROLE THEN 1
    WHEN 'user'::CHAT_ROLE THEN 2
    WHEN 'assistant'::CHAT_ROLE THEN 3
  END;

-- name: CreateMessage :one
INSERT INTO messages (conversation_id, chat_role, content, author_id)
VALUES ($1, $2, $3, $4)
RETURNING *;

-- name: CreateMessages :batchmany
INSERT INTO messages (conversation_id, chat_role, content, author_id)
VALUES ($1, $2, $3, $4)
RETURNING *;

-- name: EditMessage :one
UPDATE messages
SET content = $2
WHERE id = $1
RETURNING *;
