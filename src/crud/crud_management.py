from typing import List
from sqlalchemy import select
from fastapi import HTTPException, Depends

from src.models.request import RequestFrom, RequestStatus
from src.database import AsyncSession, get_db_session
from src.crud import CompanyCRUD, UserCRUD
from src import schemas, models


class ManagementCRUD:

    def __init__(
            self,
            db: AsyncSession = Depends(get_db_session),
            company_crud: CompanyCRUD = Depends(),
            user_crud: UserCRUD = Depends()
    ):
        self.db: AsyncSession = db
        self.company_crud = company_crud
        self.user_crud = user_crud

    async def get_invite_by_id(self, invite_id: int) -> models.Request:
        result = await self.db.execute(select(models.Request).filter(models.Request.id == invite_id))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Not Found Invite")
        return result

    async def get_invites_by_user_id(self, user_id) -> List[schemas.Invite]:
        result = list()
        invites = await self.db.execute(select(models.Request).filter(
            (models.Request.user_id == user_id) &
            (models.Request.request_from == RequestFrom.company) &
            (models.Request.status == RequestStatus.pending)
        ))
        invites = invites.scalars().all()
        for invite in invites:
            result.append(schemas.Invite(
                id=invite.id,
                status=invite.status,
                company=schemas.InviteFrom(
                    id=invite.company.id,
                    title=invite.company.title
                )
            ))
        return result

    async def get_invite_by_user_id_and_company_id(self, user_id: int, company_id: int) -> models.Request:
        result = await self.db.execute(select(models.Request).filter(
            (models.Request.user_id == user_id) & (models.Request.company_id == company_id)
        ))
        return result.scalars().first()

    async def create_invite(self, user_id: int, company_id: int, owner_id: int) -> models.Request:
        if user_id == owner_id:
            raise HTTPException(status_code=400, detail="You cannot invite yourself")

        invite_exist = await self.get_invite_by_user_id_and_company_id(user_id=user_id, company_id=company_id)
        if invite_exist:
            raise HTTPException(status_code=400, detail="The user is already invited")

        company = await self.company_crud.get_company_by_id(company_id=company_id)

        owner = await self.company_crud.get_owner_by_company_id(company_id=company_id)
        if owner.id is not owner_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        worker_exist = await self.company_crud.get_worker_by_user_id_and_company_id(user_id=user_id, company_id=company_id)
        if worker_exist:
            raise HTTPException(status_code=400, detail="The user is already an employee of the company")

        user = await self.user_crud.get_user(user_id=user_id)

        invite = models.Request(
            company=company,
            user=user,
            request_from=RequestFrom.company
        )

        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def update_invite(
            self, invite_id: int, user_id: int, status: RequestStatus
    ) -> models.Request:
        invite_exist = await self.get_invite_by_id(invite_id=invite_id)

        if invite_exist.user_id is not user_id:
            raise HTTPException(status_code=400, detail="You don't have this invite")

        invite_exist.status = status

        await self.db.commit()
        await self.db.refresh(invite_exist)
        return invite_exist

    async def get_request_by_id(self, request_id: int) -> models.Request:
        result = await self.db.execute(select(models.Request).filter(models.Request.id == request_id))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Not Found Request")
        return result

    async def get_requests_by_company_id_and_status(
            self, company_id: int, status: RequestStatus
    ) -> List[models.Request]:
        result = await self.db.execute(select(models.Request).filter(
            (models.Request.company_id == company_id) &
            (models.Request.status == status) &
            (models.Request.request_from == RequestFrom.user)
        ))
        return result.scalars().all()

    async def get_all_requests_to_companies(
            self, owner_id: int
    ) -> List[schemas.Request]:
        result = list()
        where_im_owner = await self.company_crud.get_company_where_im_owner(user_id=owner_id)
        for company in where_im_owner:
            requests = await self.get_requests_by_company_id_and_status(
                company_id=company.id, status=RequestStatus.pending
            )
            for request in requests:
                result.append(schemas.Request(
                        id=request.id,
                        status=request.status,
                        from_user=schemas.RequestFrom(
                            id=request.user_id,
                            email=request.user.email
                        ),
                        to_company=schemas.RequestTo(
                            id=request.company_id,
                            title=company.title
                        )
                    )
                )
        return result

    async def get_request_by_user_id_and_company_id(self, user_id: int, company_id: int) -> models.Request:
        result = await self.db.execute(select(models.Request).filter(
                (models.Request.company_id == company_id) &
                (models.Request.user_id == user_id) &
                (models.Request.request_from == RequestFrom.user)
            )
        )
        return result.scalars().first()

    async def create_request(self, company_id: int, user_id: int) -> models.Request:
        request_exist = await self.get_request_by_user_id_and_company_id(
            user_id=user_id, company_id=company_id
        )
        if request_exist:
            raise HTTPException(status_code=400, detail="The request has already been sent")

        company = await self.company_crud.get_company_by_id(company_id=company_id)

        worker_exist = await self.company_crud.get_worker_by_user_id_and_company_id(
            user_id=user_id, company_id=company_id
        )
        if worker_exist:
            raise HTTPException(status_code=400, detail="The user is already an employee of the company")

        user = await self.user_crud.get_user(user_id=user_id)

        request = models.Request(
            company=company,
            user=user,
            request_from=RequestFrom.user
        )

        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def update_request(
            self, request_id: int, owner_id: int, status: RequestStatus
    ) -> models.Request:
        request_exist = await self.get_request_by_id(request_id=request_id)

        owner = await self.company_crud.get_owner_by_company_id(company_id=request_exist.company_id)
        if owner.id is not owner_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this company")

        request_exist.status = status

        await self.db.commit()
        await self.db.refresh(request_exist)
        return request_exist
