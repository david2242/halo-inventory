"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- locations ---
    op.create_table(
        "locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_locations_name"),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column(
            "role",
            sa.Enum("director", "delegate", name="user_role"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # --- equipment ---
    op.create_table(
        "equipment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "laptop", "desktop", "printer", "phone",
                "tablet", "monitor", "projector", "other",
                name="equipment_category",
            ),
            nullable=False,
        ),
        sa.Column("manufacturer", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("qr_code", sa.String(36), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column("room", sa.String(100), nullable=True),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "retired", name="equipment_status"),
            nullable=False,
            server_default=sa.text("'active'::equipment_status"),
        ),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by_id", sa.UUID(), nullable=True),
        sa.Column("retirement_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["retired_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_qr_code", "equipment", ["qr_code"], unique=True)
    op.create_index("ix_equipment_location_status", "equipment", ["location_id", "status"])
    op.execute(
        "CREATE UNIQUE INDEX ix_equipment_serial_number_not_null "
        "ON equipment (serial_number) WHERE serial_number IS NOT NULL"
    )

    # --- audit_sessions ---
    op.create_table(
        "audit_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column("started_by_id", sa.UUID(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("in_progress", "completed", name="audit_session_status"),
            nullable=False,
            server_default=sa.text("'in_progress'::audit_session_status"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["started_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_sessions_location_status", "audit_sessions", ["location_id", "status"])
    op.execute(
        "CREATE UNIQUE INDEX ix_audit_sessions_one_open_per_location "
        "ON audit_sessions (location_id) WHERE status = 'in_progress'"
    )

    # --- audit_items ---
    op.create_table(
        "audit_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("audit_session_id", sa.UUID(), nullable=False),
        sa.Column("equipment_id", sa.UUID(), nullable=False),
        sa.Column(
            "check_method",
            sa.Enum("scan", "manual", name="check_method"),
            nullable=True,
        ),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_present", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["audit_session_id"], ["audit_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_session_id", "equipment_id", name="uq_audit_items_session_equipment"),
    )
    op.create_index("ix_audit_items_session_id", "audit_items", ["audit_session_id"])


def downgrade() -> None:
    op.drop_table("audit_items")
    op.drop_table("audit_sessions")
    op.drop_table("equipment")
    op.drop_table("users")
    op.drop_table("locations")
    op.execute("DROP TYPE IF EXISTS check_method")
    op.execute("DROP TYPE IF EXISTS audit_session_status")
    op.execute("DROP TYPE IF EXISTS equipment_status")
    op.execute("DROP TYPE IF EXISTS equipment_category")
    op.execute("DROP TYPE IF EXISTS user_role")
