from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .worker import Worker
from src.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String)
    description = Column(String)
    passing_frequency = Column(Integer)
    number_of_questions = Column(Integer)

    company = relationship("Company", back_populates="quizzes", lazy='selectin')
    questions = relationship("Question", back_populates="quiz", lazy='selectin')
    quizzes_results = relationship("QuizResult", back_populates="quiz", lazy='selectin')


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question = Column(String)

    quiz = relationship("Quiz", back_populates="questions", lazy='selectin')
    answers = relationship("Answer", back_populates="question", lazy='selectin')


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer = Column(String)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="answers", lazy='selectin')


class GeneralResult(Base):
    __tablename__ = "general_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    gpa = Column(Float)
    update_date = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="general_results", lazy='selectin')
    company = relationship("Company", back_populates="general_results", lazy='selectin')
    quizzes_results = relationship("QuizResult", back_populates="general_result", lazy='selectin')


class QuizResult(Base):
    __tablename__ = "quizzes_results"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    general_result_id = Column(Integer, ForeignKey("general_results.id"))
    correct_answers = Column(Integer)
    gpa = Column(Float)
    date_of_passage = Column(DateTime(timezone=True), default=func.now())

    quiz = relationship("Quiz", back_populates="quizzes_results", lazy='selectin')
    general_result = relationship("GeneralResult", back_populates="quizzes_results", lazy='selectin')
