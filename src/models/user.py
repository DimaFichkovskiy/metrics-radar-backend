from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, default=None)
    last_name = Column(String, default=None)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, default=None)
    date_created = Column(DateTime(timezone=True), default=func.now())

    workers = relationship("Worker", back_populates="user", lazy='selectin')
    requests = relationship("Request", back_populates="user", lazy='selectin')
    general_results = relationship("GeneralResult", back_populates="user", lazy='selectin')
