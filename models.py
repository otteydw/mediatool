import enum

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from utils import MediaType


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    filetype: Mapped[enum.Enum] = mapped_column(Enum(MediaType), nullable=True)

    def __repr__(self):
        return f"File: {self.name}\nSize {self.size}\nSHA256: {self.sha256}"
