import enum

from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref

from src.database import Base


class Role(enum.Enum):
    owner = 2
    admin = 1
    staff = 0


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    role = Column(Enum(Role), default=Role.staff)

    user = relationship("User", back_populates="workers", lazy='selectin')
    company = relationship("Company", back_populates="workers", lazy='selectin')

