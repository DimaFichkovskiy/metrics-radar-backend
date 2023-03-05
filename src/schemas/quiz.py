from typing import List, Optional
from pydantic import BaseModel, validator
from fastapi import HTTPException
from datetime import datetime


class Question(BaseModel):
    question: str
    answer_options: list
    correct_answer: int

    @validator('answer_options')
    def number_of_answers(cls, v):
        if len(v) < 2:
            raise HTTPException(status_code=400, detail="Not enough answers")
        return v


class Quiz(BaseModel):
    id: int
    title: str
    description: str
    passing_frequency: int
    number_of_questions: int

    class Config:
        orm_mode = True


class CreateQuiz(BaseModel):
    title: str
    description: str
    passing_frequency: int
    list_questions: List[Question]

    @validator('list_questions')
    def number_of_questions(cls, v):
        if len(v) < 2:
            raise HTTPException(status_code=400, detail="Not enough questions")
        return v


class AnswerResponse(BaseModel):
    id: int
    answer: str
    is_correct: bool

    class Config:
        orm_mode = True


class QuestionsResponse(BaseModel):
    id: int
    question: str
    answer_options: List[AnswerResponse]

    class Config:
        orm_mode = True


class QuizResponse(BaseModel):
    id: int
    title: str
    description: str
    passing_frequency: int
    number_of_questions: int
    list_questions: List[QuestionsResponse]

    class Config:
        orm_mode = True


class AnswersFromUser(BaseModel):
    question_id: int
    answer_id: int


class TestResponse(BaseModel):
    quiz_id: int
    number_of_questions: int
    correct_answers: int
    gpa: float

    class Config:
        orm_mode = True


class UserGPAResponse(BaseModel):
    user_id: int
    gpa: float


class UserGPAQuizResponse(BaseModel):
    user_id: int
    quiz_id: int
    gpa: float


class UserWithTimeOfLastTestResponse(BaseModel):
    user_id: int
    time: Optional[datetime] = None


class MyGPA(BaseModel):
    company_id: int
    gpa: float


class QuizWithTimeOfLastTestResponse(BaseModel):
    quiz_id: int
    time: datetime
