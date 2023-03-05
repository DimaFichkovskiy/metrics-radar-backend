from typing import List
from sqlalchemy import select
from fastapi import HTTPException, Depends

from src.database import AsyncSession, get_db_session
from src.models.worker import Role
from src import schemas, models


class CompanyCRUD:

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db: AsyncSession = db

    async def get_company_by_id(self, company_id: int) -> models.Company:
        result = await self.db.execute(select(models.Company).filter(models.Company.id == company_id))
        result = result.scalars().first()
        if result is None:
            raise HTTPException(status_code=404, detail="Not Found Company")
        return result

    async def get_companies_by_user_id(self, user_id: int) -> List[models.Company]:
        result = await self.db.execute(select(models.Company).join(models.Worker).filter(
            models.Worker.user_id == user_id
        ))
        return result.scalars().all()

    async def get_all_public_companies(self, skip: int = 0, limit: int = 100) -> List[models.Company]:
        result = await self.db.execute(select(models.Company).filter(
            models.Company.hidden == False
        ).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_workers_by_company_id(self, company_id: int) -> List[models.Worker]:
        result = await self.db.execute(select(models.Worker).filter(models.Worker.company_id == company_id))
        return result.scalars().all()

    async def get_owner_by_company_id(self, company_id: int) -> models.User:
        result = await self.db.execute(select(models.User).join(models.Worker).filter(
            (models.Worker.company_id == company_id) & (models.Worker.role == Role.owner)
        ))
        return result.scalars().first()

    async def get_company_where_im_owner(self, user_id) -> List[models.Worker]:
        result = await self.db.execute(select(models.Company).join(models.Worker).filter(
            (models.Worker.user_id == user_id) & (models.Worker.role == Role.owner)
        ))
        return result.scalars().all()

    async def get_company_where_im_owner_or_admin_by_company_id(self, company_id: int, user_id: int) -> models.Company:
        result = await self.db.execute(select(models.Company).join(models.Worker).filter(
            (models.Company.id == company_id) &
            (models.Worker.user_id == user_id) &
            ((models.Worker.role == Role.owner) | (models.Worker.role == Role.admin))
        ))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="You are not owner or admin in this company")
        return result

    async def get_worker_by_user_id_and_company_id(self, user_id: int, company_id: int) -> models.Worker:
        result = await self.db.execute(select(models.Worker).filter(
            (models.Worker.user_id == user_id) & (models.Worker.company_id == company_id)
        ))
        return result.scalars().first()

    async def create_company(self, company_data: schemas.CreateCompany, user: schemas.User) -> models.Company:

        company = models.Company(
            title=company_data.title,
            description=company_data.description
        )

        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)

        await self.create_worker_in_company(
            company=company,
            user=user,
            role=Role.owner
        )
        return company

    async def create_worker_in_company(self, company: models.Company, user: models.User, role: Role) -> models.Worker:
        worker = models.Worker(
            company=company,
            user=user,
            role=role
        )

        self.db.add(worker)
        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def update_worker_admin(self, user_id: int, company_id: int, owner_id: int, role: Role) -> models.Worker:
        company = await self.get_company_by_id(company_id=company_id)

        owner = await self.get_owner_by_company_id(company_id=company.id)
        if owner.id is not owner_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        worker = await self.get_worker_by_user_id_and_company_id(user_id=user_id, company_id=company_id)
        if worker is None:
            raise HTTPException(status_code=404, detail="Not Found Worker")

        worker.role = role

        await self.db.commit()
        await self.db.refresh(worker)
        return worker

    async def update_company_status(
            self, company_id: int, user_id: int, change_data: schemas.ChangeCompanyStatus
    ) -> schemas.Company:
        company = await self.get_company_by_id(company_id=company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Not Found Company")

        owner = await self.get_owner_by_company_id(company_id=company_id)
        if owner.id is not user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        company.hidden = change_data.hidden

        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def update_company_info(
            self, company_id: int, user_id, update_data: schemas.CompanyInfoUpdate
    ) -> schemas.Company:
        if (update_data.title and update_data.description) is None:
            raise HTTPException(status_code=400, detail="There is not enough data to update")

        company = await self.get_company_by_id(company_id=company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Not Found Company")

        owner = await self.get_owner_by_company_id(company_id=company_id)
        if owner.id is not user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        if update_data.title:
            company.title = update_data.title
        if update_data.description:
            company.description = update_data.description

        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def delete_company(self, company_id: int, user_id: int):
        company = await self.get_company_by_id(company_id=company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Not Found Company")

        owner = await self.get_owner_by_company_id(company_id=company_id)
        if owner.id is not user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        await self.delete_all_workers_in_company(company_id=company.id)
        await self.db.delete(company)
        await self.db.commit()

    async def delete_all_workers_in_company(self, company_id: int):
        result = await self.db.execute(select(models.Worker).filter(models.Worker.company_id == company_id))
        workers = result.scalars().all()
        for worker in workers:
            await self.db.delete(worker)
            await self.db.commit()

    async def delete_worker(self, company_id: int, user_id: int, owner_id: int):
        if user_id == owner_id:
            raise HTTPException(status_code=400, detail="You cannot delete yourself")

        company = await self.get_company_by_id(company_id=company_id)

        owner = await self.get_owner_by_company_id(company_id=company.id)
        if owner.id is not owner_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        worker = await self.get_worker_by_user_id_and_company_id(user_id=user_id, company_id=company_id)
        if worker is None:
            raise HTTPException(status_code=404, detail="Not Found Worker")

        await self.db.delete(worker)
        await self.db.commit()
