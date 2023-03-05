from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, paginate

from src import schemas
from src.crud import QuizCrud
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"],
    responses={404: {"description": "Not Found"}}
)


@router.get("/all_quizzes", response_model=Page[schemas.Quiz], status_code=status.HTTP_200_OK)
async def get_all_quizzes_for_company(
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        quiz_crud: QuizCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
):
    quizzes = await quiz_crud.get_all_quizzes(company_id=company_id, skip=skip, limit=limit)
    return paginate(quizzes)


@router.post("/create", response_model=schemas.QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
        company_id: int,
        quiz_data: schemas.CreateQuiz,
        quiz_crud: QuizCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.QuizResponse:
    quiz = await quiz_crud.create_quiz(quiz_data=quiz_data, user_id=current_user.id, company_id=company_id)

    return quiz


@router.patch("/add_questions_to_quiz", response_model=schemas.QuizResponse, status_code=status.HTTP_201_CREATED)
async def add_questions_to_quiz(
        company_id: int,
        quiz_id: int,
        questions_data: List[schemas.Question],
        quiz_crud: QuizCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.QuizResponse:
    updated_quiz = await quiz_crud.add_questions_to_quiz(
        questions_data=questions_data, company_id=company_id, quiz_id=quiz_id, user_id=current_user.id
    )

    return updated_quiz


@router.patch("/remove_question_from_quiz", response_model=schemas.QuizResponse, status_code=status.HTTP_201_CREATED)
async def remove_question_from_quiz(
        company_id: int,
        quiz_id: int,
        question_id: int,
        quiz_crud: QuizCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.QuizResponse:
    updated_quiz = await quiz_crud.remove_question_from_quiz(
        company_id=company_id, user_id=current_user.id, quiz_id=quiz_id, question_id=question_id
    )

    return updated_quiz


@router.delete("/delete", response_model=schemas.Response, status_code=status.HTTP_200_OK)
async def delete_quiz(
        company_id: int,
        quiz_id: int,
        quiz_crud: QuizCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
):
    await quiz_crud.delete_quiz(user_id=current_user.id, company_id=company_id, quiz_id=quiz_id)
    return schemas.Response(
        status_code=status.HTTP_200_OK,
        body="Success delete quiz"
    )
