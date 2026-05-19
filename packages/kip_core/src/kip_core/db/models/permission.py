import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kip_core.db.base import Base

if TYPE_CHECKING:
    from kip_core.db.models.document import Document


class PermissionMapping(Base):
    __tablename__ = "permission_mappings"
    __table_args__ = (
        UniqueConstraint("document_id", "principal", name="uq_permission_document_principal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    principal: Mapped[str] = mapped_column(String(320), nullable=False)
    permission_level: Mapped[str] = mapped_column(String(32), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="permissions")
