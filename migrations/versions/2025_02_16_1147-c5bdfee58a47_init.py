"""init

Revision ID: c5bdfee58a47
Revises:
Create Date: 2025-02-16 11:47:55.123456

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5bdfee58a47"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("""
        CREATE TABLE conversations (
            id VARCHAR(26) NOT NULL DEFAULT idkit_ulid_generate(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            guild_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,

            CONSTRAINT conversations_pk PRIMARY KEY (id),
            CONSTRAINT conversations_guild_id_channel_id_uq UNIQUE (guild_id, channel_id)
        )
        """)
    )

    conn.execute(sa.text("CREATE INDEX conversations_id_ix ON conversations (id)"))
    conn.execute(
        sa.text("CREATE INDEX conversations_guild_id_ix ON conversations (guild_id)")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX conversations_channel_id_ix ON conversations (channel_id)"
        )
    )

    conn.execute(
        sa.text("CREATE TYPE CHAT_ROLE AS ENUM ('user', 'assistant', 'system')")
    )

    conn.execute(
        sa.text("""
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
                (author_id IS NULL AND chat_role <> 'user')
                OR (author_id IS NOT NULL AND chat_role = 'user')
            )
        )
        """)
    )

    conn.execute(sa.text("CREATE INDEX messages_id_ix ON messages (id)"))
    conn.execute(
        sa.text(
            "CREATE INDEX messages_conversation_id_ix ON messages (conversation_id)"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DROP TABLE IF EXISTS messages"))
    conn.execute(sa.text("DROP TABLE IF EXISTS conversations"))
    conn.execute(sa.text("DROP TYPE IF EXISTS CHAT_ROLE"))
