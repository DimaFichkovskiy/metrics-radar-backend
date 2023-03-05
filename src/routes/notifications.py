from typing import List
from fastapi import APIRouter, Depends, status

from src import schemas, models
from src.crud import CompanyCRUD, ManagementCRUD
from src.database import AsyncSession, get_db_session
from src.models.request import RequestStatus
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not Found"}}
)


@router.get("/invitations", response_model=List[schemas.Invite], status_code=status.HTTP_200_OK)
async def read_all_invitations(
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> List[schemas.Invite]:
    invites = await management_crud.get_invites_by_user_id(user_id=current_user.id)
    return invites


@router.get("/request_to_company", response_model=List[schemas.Request], status_code=status.HTTP_200_OK)
async def request_for_join_to_company(
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> List[schemas.Request]:
    requests = await management_crud.get_all_requests_to_companies(owner_id=current_user.id)
    return requests
