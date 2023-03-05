from typing import List
from fastapi import APIRouter, Depends, status

from src import schemas, models
from src.crud import WorkflowCrud
from src.database import AsyncSession, get_db_session
from src.models.request import RequestStatus
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/export",
    tags=["data_export"],
    responses={404: {"description": "Not Found"}}
)


@router.get("/my_quizzes_results")
async def my_quizzes_result(
        workflow_crud: WorkflowCrud = Depends(),
        current_user: schemas.User = Depends(get_current_user)
):
    print(current_user)
    await workflow_crud.export_my_quizzes_results(user_id=current_user.id)
