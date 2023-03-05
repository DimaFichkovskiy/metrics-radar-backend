from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .worker import Worker
from src.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    hidden = Column(Boolean, default=False)

    workers = relationship("Worker", back_populates="company", lazy='selectin')
    requests = relationship("Request", back_populates="company", lazy='selectin')
    quizzes = relationship("Quiz", back_populates="company", lazy='selectin')
    general_results = relationship("GeneralResult", back_populates="company", lazy='selectin')
