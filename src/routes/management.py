from fastapi import APIRouter, Depends, HTTPException, Response, status

from src import schemas, models
from src.crud import ManagementCRUD, UserCRUD, CompanyCRUD
from src.database import AsyncSession, get_db_session
from src.models.request import RequestStatus, RequestFrom
from src.models.worker import Role
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/management",
    tags=["management"],
    responses={404: {"description": "Not Found"}}
)


@router.post("/create_invite", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def create_invite_to_company(
        company_id: int,
        user_id: int,
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    await management_crud.create_invite(
        user_id=user_id, company_id=company_id, owner_id=current_user.id
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Success created invite"
    )


@router.patch("/accept_invite", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def accept_invite_to_company(
        invite_id: int,
        company_crud: CompanyCRUD = Depends(),
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    result_update = await management_crud.update_invite(
        invite_id=invite_id, user_id=current_user.id, status=RequestStatus.accepted
    )
    company = await company_crud.get_company_by_id(company_id=result_update.company_id)
    await company_crud.create_worker_in_company(
        company=company, user=current_user, role=Role.staff
    )

    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Invitation successfully accepted"
    )


@router.patch("/cancel_invite", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def cancel_invite_to_company(
        invite_id: int,
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    await management_crud.update_invite(
        invite_id=invite_id, user_id=current_user.id, status=RequestStatus.rejected
    )

    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Invitation successfully rejected"
    )


@router.patch("/assign_admin", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def assign_admin_to_company(
        user_id: int,
        company_id: int,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    await company_crud.update_worker_admin(
        user_id=user_id, company_id=company_id, owner_id=current_user.id, role=Role.admin
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Admin successfully added"
    )


@router.patch("/remove_admin", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def remove_admin_from_company(
        user_id: int,
        company_id: int,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    await company_crud.update_worker_admin(
        user_id=user_id, company_id=company_id, owner_id=current_user.id, role=Role.staff
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Admin successfully removed"
    )


@router.post("/apply_to_join", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def apply_to_join_the_company(
        company_id: int,
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    await management_crud.create_request(
        user_id=current_user.id, company_id=company_id
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Success created request"
    )


@router.patch("/accept_joining", response_model=schemas.Response, status_code=status.HTTP_201_CREATED)
async def accept_joining_to_company(
        request_id: int,
        company_crud: CompanyCRUD = Depends(),
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.Response:
    result_update = await management_crud.update_request(
        request_id=request_id, owner_id=current_user.id, status=RequestStatus.accepted
    )
    company = await company_crud.get_company_by_id(company_id=result_update.company_id)
    await company_crud.create_worker_in_company(
        company=company, user=result_update.user, role=Role.staff
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Request successfully accepted"
    )


@router.patch("/cancel_joining")
async def cancel_joining_to_company(
        request_id: int,
        management_crud: ManagementCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    await management_crud.update_request(
        request_id=request_id, owner_id=current_user.id, status=RequestStatus.rejected
    )
    return schemas.Response(
        status_code=status.HTTP_201_CREATED,
        body="Request successfully rejected"
    )


@router.delete("/delete_worker", response_model=schemas.Response, status_code=status.HTTP_200_OK)
async def delete_worker_from_company(
        company_id: int,
        user_id: int,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    await company_crud.delete_worker(
        company_id=company_id, user_id=user_id, owner_id=current_user.id
    )
    return schemas.Response(
        status_code=status.HTTP_200_OK,
        body="Success delete worker"
    )
