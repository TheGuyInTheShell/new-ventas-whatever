from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import BasicBaseAsync


class ImageFile(BasicBaseAsync):

    __tablename__ = "image_files"

    context: Mapped[str] = mapped_column(String, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)

    url: Mapped[str] = mapped_column(String, nullable=False)

    id_file: Mapped[str] = mapped_column(String, nullable=False)

    size: Mapped[str] = mapped_column(String, nullable=False)

    mime_type: Mapped[str] = mapped_column(String, nullable=False)
