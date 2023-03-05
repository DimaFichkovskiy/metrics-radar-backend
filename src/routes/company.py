from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, paginate

from src import schemas, models
from src.crud import CompanyCRUD
from src.database import AsyncSession, get_db_session
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/company",
    tags=["company"],
    responses={404: {"description": "Not Found"}}
)


@router.get("/all_companies", response_model=Page[schemas.Company], status_code=status.HTTP_200_OK)
async def get_all_companies(
        skip: int = 0,
        limit: int = 100,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.Company = Depends(get_current_user)
):
    companies = await company_crud.get_all_public_companies(skip=skip, limit=limit)
    return paginate(companies)


@router.get("/my", response_model=List[schemas.Company], status_code=status.HTTP_200_OK)
async def get_my_companies(
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> List[schemas.Company]:
    return await company_crud.get_companies_by_user_id(user_id=current_user.id)


@router.post("/create", response_model=schemas.Company, status_code=status.HTTP_201_CREATED)
async def create_company(
        company_data: schemas.CreateCompany,
        company_crud: CompanyCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.Company:
    return await company_crud.create_company(company_data=company_data, user=current_user)


@router.patch("/change_status", response_model=schemas.Company, status_code=status.HTTP_201_CREATED)
async def change_company_status(
        company_id: int,
        change_data: schemas.ChangeCompanyStatus,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
 ) -> schemas.Company:
    return await company_crud.update_company_status(
        company_id=company_id, user_id=current_user.id, change_data=change_data
    )


@router.patch("/update_info", response_model=schemas.Company, status_code=status.HTTP_201_CREATED)
async def update_company_info(
        company_id: int,
        update_data: schemas.CompanyInfoUpdate,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
):
    return await company_crud.update_company_info(
        company_id=company_id, user_id=current_user.id, update_data=update_data
    )


@router.delete("/delete", response_model=schemas.CompanyDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_company(
        company_id: int,
        company_crud: CompanyCRUD = Depends(),
        current_user: models.User = Depends(get_current_user)
) -> schemas.CompanyDeleteResponse:
    await company_crud.delete_company(company_id=company_id, user_id=current_user.id)
    return schemas.CompanyDeleteResponse(
        status_code=status.HTTP_200_OK,
        body="Success delete company"
    )

