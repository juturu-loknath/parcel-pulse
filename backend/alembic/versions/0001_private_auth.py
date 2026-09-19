"""Create the empty-cloud schema for private authentication and parcels."""
from alembic import op
import sqlalchemy as sa

revision = "0001_private_auth"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("username", sa.String(length=64), nullable=False), sa.Column("password_hash", sa.String(length=512), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("login_attempts", sa.Column("key", sa.String(length=64), primary_key=True), sa.Column("failures", sa.Integer(), nullable=False), sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True))
    op.create_table("parcels", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False), sa.Column("tracking_number", sa.String(length=16), nullable=False), sa.Column("mobile_number", sa.String(length=10), nullable=False), sa.Column("provider", sa.String(length=32), nullable=False), sa.Column("origin", sa.String(length=120), nullable=True), sa.Column("destination", sa.String(length=120), nullable=True), sa.Column("current_status", sa.String(length=120), nullable=False), sa.Column("events", sa.JSON(), nullable=False), sa.Column("last_successful_check", sa.DateTime(timezone=True), nullable=False), sa.Column("monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.false()), sa.UniqueConstraint("user_id", "tracking_number", "provider", name="uq_user_parcel"))
    op.create_index("ix_parcels_user_id", "parcels", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_parcels_user_id", table_name="parcels")
    op.drop_table("parcels")
    op.drop_table("login_attempts")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
