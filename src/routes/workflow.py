from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, paginate

from src import schemas
from src.crud import WorkflowCrud
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/workflow",
    tags=["workflow"],
    responses={404: {"description": "Not Found"}}
)


@router.post("/test", response_model=schemas.TestResponse, status_code=status.HTTP_201_CREATED)
async def passing_the_test(
        company_id: int,
        quiz_id: int,
        answers_data: List[schemas.AnswersFromUser],
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.TestResponse:
    general_result = await workflow_crud.get_general_result_by_user_and_company_id(
        user_id=current_user.id, company_id=company_id
    )

    if not general_result:
        general_result = await workflow_crud.create_general_result_for_user(
            answers_from_user=answers_data, company_id=company_id, quiz_id=quiz_id, user_id=current_user.id
        )

    else:
        general_result = await workflow_crud.update_general_result_for_user(
            answers_from_user=answers_data, company_id=company_id, quiz_id=quiz_id, user_id=current_user.id
        )

    return general_result


@router.get("/gpa_all_users", response_model=List[schemas.UserGPAResponse], status_code=status.HTTP_200_OK)
async def read_gpa_all_users(
        company_id: int,
        time_in_hours: int,
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> List[schemas.UserGPAResponse]:
    list_gpa_all_users = await workflow_crud.get_gpa_for_all_user(
        company_id=company_id, time_in_hours=time_in_hours, user_id=current_user.id
    )

    return list_gpa_all_users


@router.get("/gpa_all_user_quizzes", response_model=List[schemas.UserGPAQuizResponse], status_code=status.HTTP_200_OK)
async def read_gpa_all_user_quizzes(
        company_id: int,
        user_id: int,
        time_in_hours: int,
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> List[schemas.UserGPAQuizResponse]:
    list_gpa_all_user_quizzes = await workflow_crud.get_gpa_all_user_quizzes(
        company_id=company_id, worker_id=user_id, time_in_hours=time_in_hours, user_id=current_user.id
    )
    return list_gpa_all_user_quizzes


@router.get(
    "/users_with_time_last_test",
    response_model=List[schemas.UserWithTimeOfLastTestResponse],
    status_code=status.HTTP_200_OK
)
async def read_users_with_time_of_last_test(
        company_id: int,
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> List[schemas.UserWithTimeOfLastTestResponse]:
    users = await workflow_crud.get_users_with_time_of_last_test(company_id=company_id, user_id=current_user.id)

    return users


@router.get("/my_gpa", response_model=List[schemas.MyGPA], status_code=status.HTTP_200_OK)
async def read_my_gpa(
        time_in_hours: int,
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> List[schemas.MyGPA]:
    my_gpa = await workflow_crud.get_my_gpa(user_id=current_user.id, time_in_hours=time_in_hours)

    return my_gpa


@router.get(
    "/my_quizzes_with_time_last_test",
    response_model=List[schemas.QuizWithTimeOfLastTestResponse],
    status_code=status.HTTP_200_OK
)
async def read_my_quizzes_with_time_last_test(
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> List[schemas.QuizWithTimeOfLastTestResponse]:
    my_quizzes = await workflow_crud.get_my_quizzes_with_time_of_last_test(user_id=current_user.id)

    return my_quizzes
