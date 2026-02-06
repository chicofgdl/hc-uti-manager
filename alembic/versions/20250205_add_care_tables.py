"""create care domain tables

Revision ID: care_domain_20250205
Revises: 8a2efbe37bb6
Create Date: 2026-02-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "care_domain_20250205"
down_revision: Union[str, Sequence[str], None] = "8a2efbe37bb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum("ICU", "SURGICAL_CENTER", name="role")
    bed_availability = sa.Enum("NAO_DISPONIVEL", "DISPONIVEL", name="bedavailability")
    bed_occupancy = sa.Enum("LIVRE", "OCUPADO", name="bedoccupancy")
    reservation_status = sa.Enum("PENDENTE", "ACEITA", "NEGADA", "CANCELADA", name="reservationstatus")
    transfer_status = sa.Enum("PENDENTE", "ACEITA", "NEGADA", "CANCELADA", name="transferstatus")
    notification_type = sa.Enum(
        "RESERVA_CRIADA",
        "RESERVA_ATUALIZADA",
        "TRANSFERENCIA_CRIADA",
        "TRANSFERENCIA_ATUALIZADA",
        name="notificationtype",
    )

    role_enum.create(op.get_bind(), checkfirst=True)
    bed_availability.create(op.get_bind(), checkfirst=True)
    bed_occupancy.create(op.get_bind(), checkfirst=True)
    reservation_status.create(op.get_bind(), checkfirst=True)
    transfer_status.create(op.get_bind(), checkfirst=True)
    notification_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "beds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("availability_status", bed_availability, nullable=False, server_default="NAO_DISPONIVEL"),
        sa.Column("occupancy_status", bed_occupancy, nullable=False, server_default="LIVRE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_beds_code"),
    )
    op.create_index("ix_beds_id", "beds", ["id"])
    op.create_index("ix_beds_code", "beds", ["code"])

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("current_bed_id", sa.Integer(), sa.ForeignKey("beds.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("external_id", name="uq_patients_external_id"),
    )
    op.create_index("ix_patients_id", "patients", ["id"])
    op.create_index("ix_patients_external_id", "patients", ["external_id"])

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("status", reservation_status, nullable=False, server_default="PENDENTE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("preferred_datetime", sa.DateTime(), nullable=True),
        sa.Column("bed_id", sa.Integer(), sa.ForeignKey("beds.id"), nullable=True),
        sa.Column("requested_by", role_enum, nullable=False, server_default="SURGICAL_CENTER"),
        sa.Column("cancellation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_reservations_id", "reservations", ["id"])
    op.create_index("ix_reservations_patient_id", "reservations", ["patient_id"])

    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("reservations.id"), nullable=True),
        sa.Column("bed_id", sa.Integer(), sa.ForeignKey("beds.id"), nullable=True),
        sa.Column("status", transfer_status, nullable=False, server_default="PENDENTE"),
        sa.Column("requested_by", role_enum, nullable=False, server_default="SURGICAL_CENTER"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_transfers_id", "transfers", ["id"])
    op.create_index("ix_transfers_patient_id", "transfers", ["patient_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("recipient_role", role_enum, nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_recipient_role", "notifications", ["recipient_role"])


def downgrade() -> None:
    op.drop_index("ix_notifications_recipient_role", table_name="notifications")
    op.drop_index("ix_notifications_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_transfers_patient_id", table_name="transfers")
    op.drop_index("ix_transfers_id", table_name="transfers")
    op.drop_table("transfers")

    op.drop_index("ix_reservations_patient_id", table_name="reservations")
    op.drop_index("ix_reservations_id", table_name="reservations")
    op.drop_table("reservations")

    op.drop_index("ix_patients_external_id", table_name="patients")
    op.drop_index("ix_patients_id", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_beds_code", table_name="beds")
    op.drop_index("ix_beds_id", table_name="beds")
    op.drop_table("beds")

    for enum_name in [
        "notificationtype",
        "transferstatus",
        "reservationstatus",
        "bedoccupancy",
        "bedavailability",
        "role",
    ]:
        try:
            sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
        except Exception:
            pass
