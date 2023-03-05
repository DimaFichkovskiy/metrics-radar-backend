import enum

from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship

from src.database import Base


class RequestFrom(enum.Enum):
    user = 2
    company = 1


class RequestStatus(enum.Enum):
    accepted = 2
    rejected = 1
    pending = 0


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    request_from = Column(Enum(RequestFrom))
    status = Column(Enum(RequestStatus), default=RequestStatus.pending)

    user = relationship("User", back_populates="requests", lazy='selectin')
    company = relationship("Company", back_populates="requests", lazy='selectin')
